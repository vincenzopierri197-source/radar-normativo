from radar_normativo.analysis import analyze_item


def test_analysis_scores_relevant_tax_item_and_explains_reasons():
    item = {
        "title": "Decreto-legge: nuove disposizioni IVA e credito d'imposta",
        "summary": "Proroga della scadenza fiscale",
        "topics": ["fisco"],
        "published_at": "2026-10-20T06:00:00+00:00",
        "url": "https://example.test/atto",
        "legal_status": "qualcosa_altro",
    }

    result = analyze_item(item)

    assert result["relevance_score"] >= 60
    assert result["priority"] == "alta"
    assert result["relevance_reasons"]
    assert result["legal_status"] == "non_verificato"


def test_analysis_does_not_invent_topics_or_legal_status():
    result = analyze_item({"title": "Avviso generico"})

    assert result["topics"] == []
    assert result["relevance_score"] == 0
    assert result["priority"] == "bassa"
    assert result["legal_status"] == "non_verificato"
    assert "richiedono verifica" in result["legal_status_note"]


def test_analysis_classifies_from_title_when_topics_missing():
    result = analyze_item({"title": "Nuove disposizioni in materia di IVA"})

    assert "fisco" in result["topics"]
    assert result["relevance_score"] > 0
