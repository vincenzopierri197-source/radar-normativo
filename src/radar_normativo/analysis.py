"""Analisi editoriale euristica; non accerta lo stato giuridico degli atti."""
from __future__ import annotations

from typing import Any

from radar_normativo.classifier import classify_topics

# Pesi trasparenti: indicano utilità editoriale potenziale, non valore legale.
TOPIC_WEIGHTS: dict[str, int] = {
    "fisco": 16,
    "lavoro": 15,
    "previdenza": 14,
    "imprese": 13,
    "economia_finanza": 11,
    "giustizia_diritto_penale": 10,
    "ambiente_energia": 8,
}

IMPACT_TERMS: dict[str, int] = {
    "decreto-legge": 14,
    "decreto legislativo": 12,
    "legge": 8,
    "regolamento": 8,
    "obbligo": 8,
    "sanzion": 8,
    "scadenza": 7,
    "proroga": 7,
    "entra in vigore": 7,
    "credito d'imposta": 8,
    "aliquota": 6,
    "contribut": 5,
    "abrog": 8,
    "modifica": 5,
    "disposizioni": 3,
}

def analyze_item(item: dict[str, Any]) -> dict[str, Any]:
    """Aggiunge indicatori editoriali conservando lo stato giuridico non verificato.

    Il punteggio è deterministico e spiegabile. Non equivale a una valutazione
    giuridica, non conferma l'autenticità dell'atto e non verifica la vigenza.
    """
    result = dict(item)
    title = str(result.get("title") or "")
    summary = str(result.get("summary") or "")
    text = f"{title} {summary}".casefold()

    topics = result.get("topics")
    if not isinstance(topics, list):
        topics = classify_topics(title, summary)
    topics = [str(topic) for topic in topics]
    result["topics"] = topics

    score = max((TOPIC_WEIGHTS.get(topic, 0) for topic in topics), default=0)
    reasons: list[str] = []
    if topics:
        best_topic = max(topics, key=lambda topic: TOPIC_WEIGHTS.get(topic, 0))
        reasons.append(f"area tematica: {best_topic} (+{TOPIC_WEIGHTS.get(best_topic, 0)})")

    matched_terms: list[tuple[str, int]] = [
        (term, weight) for term, weight in IMPACT_TERMS.items() if term in text
    ]
    # Il contributo delle parole chiave è limitato per evitare punteggi gonfiati.
    impact_score = min(sum(weight for _, weight in matched_terms), 35)
    score += impact_score
    if matched_terms:
        terms = ", ".join(term for term, _ in matched_terms[:4])
        reasons.append(f"indicatori testuali: {terms} (+{impact_score})")

    if result.get("published_at"):
        score += 5
        reasons.append("data di pubblicazione presente (+5)")
    if result.get("url"):
        score += 5
        reasons.append("collegamento alla fonte presente (+5)")

    score = min(100, max(0, score))
    priority = "alta" if score >= 60 else "media" if score >= 30 else "bassa"

    result["analysis_version"] = 1
    result["relevance_score"] = score
    result["priority"] = priority
    result["relevance_reasons"] = reasons
    # Non promuovere mai automaticamente il contenuto a stato giuridico verificato.
    result["legal_status"] = "non_verificato"
    result["legal_status_note"] = (
        "Punteggio e classificazione sono euristici; la vigenza, le modifiche "
        "e le abrogazioni richiedono verifica su fonti ufficiali."
    )
    return result
