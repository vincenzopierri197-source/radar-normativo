"""Analisi editoriale euristica; non accerta lo stato giuridico degli atti."""
from __future__ import annotations

from typing import Any

from radar_normativo.classifier import classify_topics

# Pesi trasparenti: utilità editoriale potenziale, non valore legale.
TOPIC_WEIGHTS: dict[str, int] = {
    "fisco": 24,
    "lavoro": 23,
    "previdenza": 22,
    "imprese": 21,
    "economia_finanza": 19,
    "giustizia_diritto_penale": 17,
    "ambiente_energia": 15,
    "salute_farmaci": 20,
    "agricoltura_alimentazione": 18,
    "trasporti_infrastrutture": 17,
    "digitale_cyber": 19,
    "difesa_sicurezza": 14,
}

IMPACT_TERMS: dict[str, int] = {
    "decreto-legge": 14,
    "decreto legislativo": 12,
    "legge": 8,
    "regolamento": 8,
    "regulation": 8,
    "directive": 8,
    "decision": 4,
    "obbligo": 8,
    "obligation": 8,
    "sanzion": 8,
    "penalty": 6,
    "scadenza": 7,
    "deadline": 7,
    "proroga": 7,
    "extension": 4,
    "entra in vigore": 7,
    "entry into force": 7,
    "credito d'imposta": 8,
    "tax credit": 8,
    "aliquota": 6,
    "tax rate": 6,
    "contribut": 5,
    "abrog": 8,
    "repeal": 8,
    "modifica": 5,
    "amending": 5,
    "disposizioni": 3,
    "provision": 3,
    "implementing": 4,
}


def analyze_item(item: dict[str, Any]) -> dict[str, Any]:
    """Aggiunge indicatori editoriali spiegabili senza simulare una verifica legale.

    Il punteggio misura pertinenza tematica e segnali di impatto nel testo.
    La presenza di un URL o di una data è metadato e non aumenta la rilevanza.
    """
    result = dict(item)
    title = str(result.get("title") or "")
    summary = str(result.get("summary") or "")
    text = f"{title} {summary}".casefold()

    topics = result.get("topics")
    if not isinstance(topics, list) or not topics:
        topics = classify_topics(title, summary)
    topics = [str(topic) for topic in topics]
    result["topics"] = topics

    best_topic = max(topics, key=lambda topic: TOPIC_WEIGHTS.get(topic, 0), default=None)
    score = TOPIC_WEIGHTS.get(best_topic, 0) if best_topic else 0
    reasons: list[str] = []
    if best_topic and score:
        reasons.append(f"area tematica: {best_topic} (+{score})")

    matched_terms = [
        (term, weight) for term, weight in IMPACT_TERMS.items() if term in text
    ]
    impact_score = min(sum(weight for _, weight in matched_terms), 45)
    score += impact_score
    if matched_terms:
        terms = ", ".join(term for term, _ in matched_terms[:4])
        reasons.append(f"indicatori testuali: {terms} (+{impact_score})")

    score = min(100, max(0, score))
    priority = "alta" if score >= 60 else "media" if score >= 30 else "bassa"

    result["analysis_version"] = 2
    result["relevance_score"] = score
    result["priority"] = priority
    result["relevance_reasons"] = reasons
    result["legal_status"] = "non_verificato"
    result["legal_status_note"] = (
        "Punteggio e classificazione sono euristici; la vigenza, le modifiche "
        "e le abrogazioni richiedono verifica su fonti ufficiali."
    )
    return result
