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
    assert result["analysis_version"] == 2
    assert result["legal_status"] == "non_verificato"


def test_analysis_does_not_reward_metadata_as_relevance():
    result = analyze_item({
        "title": "Avviso generico",
        "published_at": "2026-10-20",
        "url": "https://example.test/atto",
    })

    assert result["topics"] == []
    assert result["relevance_score"] == 0
    assert result["priority"] == "bassa"
    assert result["legal_status"] == "non_verificato"


def test_analysis_classifies_from_title_when_topics_missing():
    result = analyze_item({"title": "Nuove disposizioni in materia di IVA"})

    assert "fisco" in result["topics"]
    assert result["relevance_score"] > 0


def test_analysis_reclassifies_stale_empty_topics_for_eu_items():
    result = analyze_item({
        "title": "Commission Implementing Regulation on VAT and tax credit",
        "topics": [],
        "language": "en",
    })
    assert "fisco" in result["topics"]
    assert result["priority"] in {"media", "alta"}
