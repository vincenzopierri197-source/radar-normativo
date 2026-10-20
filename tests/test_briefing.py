import pytest

from radar_normativo.briefing import render_briefing


def test_briefing_orders_high_priority_and_includes_source_and_caveat():
    items = [
        {
            "title": "Avviso generico",
            "priority": "bassa",
            "relevance_score": 5,
            "url": "https://example.test/low",
        },
        {
            "title": "Nuove disposizioni IVA",
            "priority": "alta",
            "relevance_score": 75,
            "topics": ["fisco"],
            "published_at": "2026-10-20",
            "source_name": "Fonte ufficiale di prova",
            "url": "https://example.test/high",
            "summary": "<p>Credito d'imposta &amp; proroga</p>",
        },
    ]

    result = render_briefing(items)

    assert result.index("Nuove disposizioni IVA") < result.index("Avviso generico")
    assert "Fonte: Fonte ufficiale di prova" in result
    assert "Credito d'imposta & proroga" in result
    assert "Stato giuridico: NON VERIFICATO" in result
    assert "https://example.test/high" in result


def test_briefing_handles_empty_items_and_rejects_invalid_limit():
    assert "Nessuna nuova pubblicazione" in render_briefing([])
    with pytest.raises(ValueError):
        render_briefing([], limit=0)


def test_briefing_does_not_emit_unsafe_urls():
    result = render_briefing([{"title": "Test", "url": "javascript:alert(1)"}])
    assert "javascript:" not in result
    assert "URL non disponibile" in result


def test_briefing_applies_item_limit():
    items = [
        {"title": f"Atto {i}", "priority": "bassa", "relevance_score": i}
        for i in range(5)
    ]
    result = render_briefing(items, limit=2)
    assert "Atto 4" in result
    assert "Atto 3" in result
    assert "Atto 2" not in result
