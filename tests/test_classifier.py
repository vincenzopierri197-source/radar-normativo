from radar_normativo.classifier import classify_topics


def test_classifies_tax_topics():
    assert "fisco" in classify_topics("Nuove disposizioni in materia di IVA")


def test_classifies_multiple_topics_from_summary():
    topics = classify_topics("Nuove misure", "Contributi INPS per i lavoratori e le imprese")
    assert "previdenza" in topics
    assert "lavoro" in topics
    assert "imprese" in topics


def test_classifies_english_eu_legal_titles():
    topics = classify_topics(
        "Commission Implementing Regulation on VAT and tax credit for enterprises"
    )
    assert "fisco" in topics
    assert "imprese" in topics


def test_unknown_topic_returns_empty_list():
    assert classify_topics("Avviso senza parole chiave specifiche") == []
