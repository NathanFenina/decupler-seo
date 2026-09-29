#!/usr/bin/env python3
"""PageRank interne — où va l'autorité dans votre maillage.

    python3 scripts/internal_pagerank.py crawl.csv
    python3 scripts/internal_pagerank.py crawl.csv --prioritaires /devis,/contact

Lit le CSV produit par crawl_site.py et calcule un PageRank simplifié à
partir du nombre de liens entrants et de la profondeur. Sert à répondre à
une seule question : les pages qui rapportent reçoivent-elles l'autorité ?

Sans dépendance externe.
"""

from __future__ import annotations

import argparse
import csv
import sys
from urllib.parse import urlparse

AMORTISSEMENT = 0.85
ITERATIONS = 30


def charger(chemin: str) -> list[dict]:
    with open(chemin, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def calculer(lignes: list[dict]) -> dict[str, float]:
    """PageRank approché.

    Le CSV du crawler ne conserve pas le détail des arcs, seulement les
    degrés. On approxime donc : le score d'une page dépend de son nombre de
    liens entrants, pondéré par la rareté (une page liée depuis le footer de
    tout le site n'est pas une page importante) et amortie par la profondeur.
    """
    n = len(lignes) or 1
    scores: dict[str, float] = {}

    entrants_max = max((int(l.get("liens_entrants") or 0) for l in lignes), default=1) or 1

    for ligne in lignes:
        url = ligne["url"]
        entrants = int(ligne.get("liens_entrants") or 0)
        profondeur = int(ligne.get("profondeur") or 0)

        # Un lien présent sur toutes les pages (menu, footer) porte peu de
        # signal : on écrête la contribution au-delà de 60 % du site.
        seuil_global = n * 0.6
        effectifs = min(entrants, seuil_global) if entrants > seuil_global else entrants

        base = effectifs / entrants_max
        penalite_profondeur = 1 / (1 + max(0, profondeur - 2) * 0.4)
        scores[url] = round((1 - AMORTISSEMENT) + AMORTISSEMENT * base * penalite_profondeur, 4)

    # Normalisation sur 100 pour rester lisible.
    maxi = max(scores.values(), default=1) or 1
    return {url: round(score / maxi * 100, 1) for url, score in scores.items()}


def main() -> int:
    p = argparse.ArgumentParser(description="PageRank interne")
    p.add_argument("csv", help="fichier produit par crawl_site.py")
    p.add_argument("--prioritaires", default="", help="chemins des pages qui doivent recevoir l'autorité, séparés par des virgules")
    p.add_argument("--exporter", default="autorite-interne.csv")
    args = p.parse_args()

    lignes = charger(args.csv)
    if not lignes:
        print("CSV vide.", file=sys.stderr)
        return 1

    scores = calculer(lignes)
    index = {l["url"]: l for l in lignes}
    classement = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)

    with open(args.exporter, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["url", "score_autorite", "liens_entrants", "profondeur", "mots"])
        for url, score in classement:
            l = index[url]
            w.writerow([url, score, l.get("liens_entrants"), l.get("profondeur"), l.get("mots")])

    print("\n─── Top 15 · pages qui concentrent l'autorité ───")
    for url, score in classement[:15]:
        chemin = urlparse(url).path or "/"
        print(f"  {score:>5.1f}  {index[url].get('liens_entrants'):>4} liens  {chemin[:60]}")

    prioritaires = [c.strip() for c in args.prioritaires.split(",") if c.strip()]
    if prioritaires:
        print("\n─── Vos pages prioritaires ───")
        alerte = False
        for chemin in prioritaires:
            trouvees = [(u, s) for u, s in scores.items() if urlparse(u).path.rstrip("/") == chemin.rstrip("/")]
            if not trouvees:
                print(f"  ⚠️  {chemin} — introuvable dans le crawl")
                continue
            url, score = trouvees[0]
            entrants = int(index[url].get("liens_entrants") or 0)
            rang = next(i for i, (u, _) in enumerate(classement, 1) if u == url)
            if entrants < 10:
                alerte = True
                print(f"  🔴 {chemin} — {score}/100, rang {rang}/{len(classement)}, "
                      f"{entrants} liens entrants (objectif : 10+)")
            else:
                print(f"  🟢 {chemin} — {score}/100, rang {rang}, {entrants} liens entrants")
        if alerte:
            print("\n  Les pages en rouge génèrent du chiffre et ne reçoivent pas")
            print("  d'autorité. C'est le correctif le plus rentable du maillage.")

    orphelines = [l for l in lignes if int(l.get("liens_entrants") or 0) == 0
                  and int(l.get("profondeur") or 0) > 0]
    if orphelines:
        print(f"\n🔴 {len(orphelines)} pages orphelines (aucun lien entrant).")
        for l in orphelines[:10]:
            print(f"     {urlparse(l['url']).path}")
        if len(orphelines) > 10:
            print(f"     … et {len(orphelines) - 10} autres")

    print(f"\nDétail complet dans {args.exporter}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
