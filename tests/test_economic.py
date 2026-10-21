from radar_normativo.economic import render_economic_report


def sample_rows():
    return [
        {"name": "FTSE MIB", "symbol": "FTSEMIB.MI", "region": "Italia", "ok": True, "change_pct": 1.2},
        {"name": "Dow Jones", "symbol": "^DJI", "region": "USA", "ok": True, "change_pct": 0.7},
        {"name": "China fund", "symbol": "CHINA.MI", "region": "Cina", "ok": True, "change_pct": -0.1},
        {"name": "Missing", "symbol": "MISSING", "region": "Altro", "ok": False},
    ]


def test_economic_report_explains_market_score_without_claiming_macro_data():
    text = render_economic_report("economia", sample_rows())
    assert "Punteggio indicativo:" in text
    assert "Motivo principale:" in text
    assert "nessun dato macro ufficiale" in text.lower()


def test_scenario_report_is_conditional():
    text = render_economic_report("stime", sample_rows())
    assert "SCENARI CONDIZIONALI" in text
    assert "non previsioni con probabilità statistiche" in text


def test_risk_report_reports_missing_data():
    text = render_economic_report("rischi", sample_rows())
    assert "Copertura incompleta: 1" in text
    assert "Rischi macro" in text


def test_no_data_does_not_invent_score():
    text = render_economic_report("andamento", [])
    assert "DATI INSUFFICIENTI" in text
    assert "Punteggio indicativo" not in text
