"""Classificazione tematica euristica multilingue e non giuridicamente vincolante."""
from __future__ import annotations

# Parole chiave italiane e inglesi: i feed EUR-Lex possono essere in inglese.
RULES: dict[str, tuple[str, ...]] = {
    "fisco": (
        "fisco", "tribut", "imposta", "iva", "irpef", "ires", "agenzia delle entrate",
        "accertamento fiscale", "tax", "taxation", "taxes", "vat", "value added tax",
        "income tax", "corporate tax", "excise duty", "customs duty",
    ),
    "lavoro": (
        "lavoro", "lavoratore", "lavoratori", "contratto collettivo", "licenziamento",
        "salario", "stipendio", "occupazione", "employment", "employee", "employees",
        "worker", "workers", "labour", "labor", "working conditions", "minimum wage",
    ),
    "previdenza": (
        "previdenza", "pensione", "pensioni", "inps", "contributi previdenziali",
        "ammortizzatori sociali", "social security", "social protection", "pension",
        "pensions", "unemployment benefit",
    ),
    "imprese": (
        "impresa", "imprese", "società", "societario", "camera di commercio",
        "registro delle imprese", "fallimento", "insolvenza", "company", "companies",
        "enterprise", "enterprises", "corporate", "insolvency", "bankruptcy",
        "anti-dumping", "anti dumping", "imports", "import duty",
    ),
    "economia_finanza": (
        "bilancio", "finanza", "banca", "bancario", "mercato finanziario",
        "debito pubblico", "manovra economica", "financial market", "financial markets",
        "banking", "bank", "banks", "capital market", "public debt", "budget",
        "state aid", "competition",
    ),
    "giustizia_diritto_penale": (
        "codice penale", "reato", "reati", "procedura penale", "sanzione penale",
        "giustizia", "criminal law", "criminal procedure", "court", "courts",
        "judicial", "justice", "offence", "offense", "penalty",
    ),
    "ambiente_energia": (
        "ambiente", "ambientale", "energia", "energetico", "emissioni", "rifiuti",
        "clima", "environment", "environmental", "energy", "renewable", "emissions",
        "waste", "climate", "electricity", "gas supply",
    ),
}


def classify_topics(title: str, summary: str = "") -> list[str]:
    """Restituisce tutte le categorie con corrispondenze lessicali nel testo."""
    text = f" {title} {summary} ".casefold()
    return [
        topic
        for topic, keywords in RULES.items()
        if any(keyword in text for keyword in keywords)
    ]
