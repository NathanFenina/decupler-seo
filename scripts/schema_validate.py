#!/usr/bin/env python3
"""Validation des données structurées JSON-LD.

    python3 scripts/schema_validate.py https://exemple.com/page
    python3 scripts/schema_validate.py fichier.jsonld --json

Trois niveaux : JSON valide, conformité schema.org, exigences Google.
Signale aussi les types dépréciés et les doublons.
Sans dépendance pour un fichier local ; requests + bs4 pour une URL.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Propriétés exigées par Google pour obtenir le rich result.
# Plus strictes que schema.org : un schema valide côté vocabulaire peut
# n'afficher aucun rich result s'il manque une de ces propriétés.
REQUISES_GOOGLE = {
    "Article": ["headline", "image", "datePublished", "author"],
    "NewsArticle": ["headline", "image", "datePublished", "author"],
    "BlogPosting": ["headline", "image", "datePublished", "author"],
    "Product": ["name", "image", "offers"],
    "Offer": ["price", "priceCurrency", "availability"],
    "LocalBusiness": ["name", "address", "telephone"],
    "Organization": ["name", "url"],
    "Person": ["name"],
    "BreadcrumbList": ["itemListElement"],
    "FAQPage": ["mainEntity"],
    "Question": ["name", "acceptedAnswer"],
    "VideoObject": ["name", "description", "thumbnailUrl", "uploadDate"],
    "Event": ["name", "startDate", "location"],
    "Recipe": ["name", "image", "recipeIngredient", "recipeInstructions"],
    "JobPosting": ["title", "description", "datePosted", "hiringOrganization"],
    "Course": ["name", "description", "provider"],
    "SoftwareApplication": ["name", "applicationCategory", "offers"],
}

DEPRECIES = {
    "HowTo": "Rich result déprécié en septembre 2023. Le balisage reste valide "
             "mais n'affiche plus rien dans Google.",
    "FAQPage": "Rich result restreint depuis août 2023 aux sites gouvernementaux "
               "et de santé reconnus. Reste utile pour les moteurs IA.",
    "SpecialAnnouncement": "Déprécié en juillet 2025.",
}

SENSIBLES = {
    "AggregateRating": "À n'utiliser que si les avis sont réels, visibles sur la "
                       "page et vérifiables. Une note inventée est un motif d'action manuelle.",
    "Review": "Idem : l'avis doit exister et être visible sur la page.",
}


def extraire(source: str) -> tuple[list, list[str]]:
    """Renvoie (blocs JSON-LD parsés, erreurs de parsing)."""
    chemin = Path(source)
    if chemin.exists():
        contenu = chemin.read_text(encoding="utf-8")
        try:
            return [json.loads(contenu)], []
        except json.JSONDecodeError as exc:
            return [], [f"JSON invalide : {exc}"]

    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("Pour valider une URL : pip install -r requirements.txt", file=sys.stderr)
        raise SystemExit(1)

    rep = requests.get(source, headers={"User-Agent": "ClaudeCodeSEODecupler/2.0"}, timeout=30)
    rep.raise_for_status()
    soup = BeautifulSoup(rep.text, "html.parser")

    blocs, erreurs = [], []
    for i, script in enumerate(soup.find_all("script", attrs={"type": "application/ld+json"}), 1):
        brut = script.get_text()
        try:
            blocs.append(json.loads(brut))
        except json.JSONDecodeError as exc:
            erreurs.append(f"Bloc #{i} : JSON invalide — {exc}. "
                           "Le bloc entier est ignoré par Google.")

    # Signaler les autres formats : Google recommande JSON-LD.
    if soup.find(attrs={"itemscope": True}):
        erreurs.append("Microdata détecté. Google recommande JSON-LD — "
                       "envisagez la migration.")
    if soup.find(attrs={"typeof": True}):
        erreurs.append("RDFa détecté. Google recommande JSON-LD.")

    return blocs, erreurs


def aplatir(bloc) -> list[dict]:
    """Déplie les @graph et les tableaux pour obtenir la liste des entités."""
    entites = []
    if isinstance(bloc, list):
        for item in bloc:
            entites += aplatir(item)
    elif isinstance(bloc, dict):
        if "@graph" in bloc:
            entites += aplatir(bloc["@graph"])
        if "@type" in bloc:
            entites.append(bloc)
        for valeur in bloc.values():
            if isinstance(valeur, (dict, list)) and valeur is not bloc.get("@graph"):
                entites += [e for e in aplatir(valeur) if e not in entites]
    return entites


def valider(entites: list[dict]) -> list[dict]:
    constats = []
    types_vus = []

    for entite in entites:
        types = entite.get("@type")
        types = [types] if isinstance(types, str) else (types or [])
        for t in types:
            types_vus.append(t)

            if not entite.get("@context") and "@id" not in entite:
                pass  # normal pour une entité imbriquée

            manquantes = [p for p in REQUISES_GOOGLE.get(t, []) if p not in entite]
            if manquantes:
                constats.append({
                    "gravite": "erreur", "type": t,
                    "message": f"Propriétés requises par Google manquantes : "
                               f"{', '.join(manquantes)}. Sans elles, aucun rich result.",
                })

            if t in DEPRECIES:
                constats.append({"gravite": "info", "type": t, "message": DEPRECIES[t]})
            if t in SENSIBLES:
                constats.append({"gravite": "attention", "type": t, "message": SENSIBLES[t]})

    # Doublons : très fréquent sur WordPress (plugin SEO + thème).
    for t in set(types_vus):
        if types_vus.count(t) > 1 and t in {"Article", "BlogPosting", "NewsArticle",
                                            "Organization", "WebSite", "Product"}:
            constats.append({
                "gravite": "erreur", "type": t,
                "message": f"{types_vus.count(t)} entités « {t} » sur la même page. "
                           "Google résout l'ambiguïté en les ignorant. "
                           "Cause fréquente : un plugin SEO et un thème qui posent chacun le leur.",
            })

    return constats


def main() -> int:
    p = argparse.ArgumentParser(description="Validation JSON-LD")
    p.add_argument("source", help="URL ou fichier .jsonld")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    blocs, erreurs_parsing = extraire(args.source)
    entites = [e for b in blocs for e in aplatir(b)]
    constats = valider(entites)

    types = sorted({t for e in entites for t in
                    ([e["@type"]] if isinstance(e.get("@type"), str) else e.get("@type", []))})

    if args.json:
        print(json.dumps({"types": types, "entites": len(entites),
                          "erreurs_parsing": erreurs_parsing, "constats": constats},
                         ensure_ascii=False, indent=2))
        return 0

    print(f"\n{'═' * 60}")
    print(f"  Données structurées — {len(entites)} entité(s)")
    print(f"{'═' * 60}\n")

    if not entites and not erreurs_parsing:
        print("  🔴 Aucune donnée structurée trouvée.\n")
        print("  À poser en priorité : Organization sur la home,")
        print("  BreadcrumbList partout, Article sur le contenu éditorial.\n")
        return 0

    print(f"  Types détectés : {', '.join(types) or 'aucun'}\n")

    for erreur in erreurs_parsing:
        print(f"  🔴 {erreur}\n")

    icones = {"erreur": "🔴", "attention": "🟠", "info": "ℹ️ "}
    for gravite in ("erreur", "attention", "info"):
        lot = [c for c in constats if c["gravite"] == gravite]
        for c in lot:
            print(f"  {icones[gravite]} {c['type']}")
            print(f"     {c['message']}\n")

    if not constats and not erreurs_parsing:
        print("  🟢 Aucun problème détecté.\n")

    print("  Vérifiez toujours que les valeurs du schema correspondent au")
    print("  contenu visible : un écart est un motif d'action manuelle.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
