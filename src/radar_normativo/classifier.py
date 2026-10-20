"""Classificazione tematica euristica, trasparente e non giuridicamente vincolante."""
from __future__ import annotations

RULES: dict[str, tuple[str, ...]] = {
    "fisco": ("fisco", "tribut", "imposta", "iva", "irpef", "ires", "agenzia delle entrate", "accertamento fiscale"),
    "lavoro": ("lavoro", "lavoratore", "lavoratori", "contratto collettivo", "licenziamento", "salario", "stipendio", "occupazione"),
    "previdenza": ("previdenza", "pensione", "pensioni", "inps", "contributi previdenziali", "ammortizzatori sociali"),
    "imprese": ("impresa", "imprese", "società", "societario", "camera di commercio", "registro delle imprese", "fallimento", "insolvenza"),
    "economia_finanza": ("bilancio", "finanza", "banca", "bancario", "mercato finanziario", "debito pubblico", "manovra economica"),
    "giustizia_diritto_penale": ("codice penale", "reato", "reati", "procedura penale", "sanzione penale", "giustizia"),
    "ambiente_energia": ("ambiente", "ambientale", "energia", "energetico", "emissioni", "rifiuti", "clima"),
}


def classify_topics(title: str, summary: str = "") -> list[str]:
    """Restituisce tutte le categorie con corrispondenze lessicali nel testo."""
    text = f"{title} {summary}".casefold()
    return [
        topic
        for topic, keywords in RULES.items()
        if any(keyword in text for keyword in keywords)
    ]
