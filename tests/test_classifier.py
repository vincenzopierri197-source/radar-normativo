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


def test_classifies_health_food_transport_and_digital_regulation():
    assert "salute_farmaci" in classify_topics(
        "Agenzia Italiana del Farmaco", "Autorizzazione all'immissione in commercio del medicinale"
    )
    assert "agricoltura_alimentazione" in classify_topics(
        "Commission Recommendation on monitoring nitrate and nitrite in feed"
    )
    assert "trasporti_infrastrutture" in classify_topics(
        "Disposizioni per l'impiego su strada di dispositivi di sicurezza stradale"
    )
    assert "digitale_cyber" in classify_topics(
        "Agreement on the Union Secure Connectivity Programme"
    )


def test_classifies_treasury_bonds_and_insurance():
    assert "economia_finanza" in classify_topics(
        "Ministero dell'Economia e delle Finanze", "Riapertura delle sottoscrizioni dei buoni del Tesoro poliennali"
    )
    assert "economia_finanza" in classify_topics(
        "IVASS — modifiche al registro delle imprese assicurative"
    )



def test_normalizes_whitespace_before_matching_keywords():
    topics = classify_topics(
        "Riapertura delle operazioni di sottoscrizione dei buoni del Tesoro",
        "poliennali"
    )
    assert "economia_finanza" in topics
    assert "economia_finanza" in classify_topics(
        "Titolo generico", "Riapertura dei  buoni  del Tesoro\npoliennali"
    )


def test_classifies_common_eu_agriculture_and_transport_terms():
    for title in (
        "Commission Regulation on maximum residue levels for pesticides",
        "Commission Regulation on poultry and fresh meat",
        "Commission Implementing Regulation on seed potatoes",
        "Commission Regulation on sheep pox and goat pox",
        "Commission Regulation on fishing effort",
        "Commission Regulation on food additives and curdlan",
    ):
        assert "agricoltura_alimentazione" in classify_topics(title), title
    assert "trasporti_infrastrutture" in classify_topics(
        "Regulation on mobile driving licences"
    )
