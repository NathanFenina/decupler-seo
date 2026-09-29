#!/usr/bin/env python3
"""Analyse d'un export Search Console — quick wins, CTR anormaux, cannibalisation.

    python3 scripts/gsc_analyse.py export.csv
    python3 scripts/gsc_analyse.py export.csv --conversion 0.02 --panier 800

Accepte les exports GSC standard (colonnes Page/Requête, Clics, Impressions,
CTR, Position) en français comme en anglais. Sans dépendance externe.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict

# CTR moyen attendu par position — ordres de grandeur, à ne pas prendre
# pour des vérités. Les AI Overviews écrasent ces valeurs sur les requêtes
# informationnelles : comparez vos pages entre elles avant tout.
CTR_ATTENDU = {1: 27.0, 2: 15.0, 3: 11.0, 4: 8.0, 5: 6.0, 6: 4.5,
               7: 3.5, 8: 3.0, 9: 2.5, 10: 2.0}


def ctr_attendu(position: float) -> float:
    p = int(round(position))
    if p <= 10:
        return CTR_ATTENDU.get(p, 2.0)
    return 1.2 if p <= 15 else 0.6


def normaliser_entete(nom: str) -> str:
    n = nom.strip().lower().replace("﻿", "")
    if n in ("page", "url", "pages", "landing page", "adresse"):
        return "page"
    if n in ("requête", "requete", "query", "requêtes les plus fréquentes", "mot-clé"):
        return "requete"
    if n in ("clics", "clicks", "clics url"):
        return "clics"
    if n in ("impressions", "impr."):
        return "impressions"
    if n.startswith("ctr"):
        return "ctr"
    if n.startswith("position"):
        return "position"
    return n


def nombre(valeur: str) -> float:
    v = (valeur or "0").replace(" ", "").replace("\xa0", "").replace(" ", "")
    v = v.replace("%", "").replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return 0.0


def charger(chemin: str) -> list[dict]:
    with open(chemin, newline="", encoding="utf-8-sig") as f:
        echantillon = f.read(4096)
        f.seek(0)
        delimiteur = ";" if echantillon.count(";") > echantillon.count(",") else ","
        lecteur = csv.DictReader(f, delimiter=delimiteur)
        lignes = []
        for brut in lecteur:
            ligne = {normaliser_entete(k): v for k, v in brut.items() if k}
            for champ in ("clics", "impressions", "ctr", "position"):
                ligne[champ] = nombre(ligne.get(champ, "0"))
            lignes.append(ligne)
        return lignes


def main() -> int:
    p = argparse.ArgumentParser(description="Analyse d'un export Search Console")
    p.add_argument("csv")
    p.add_argument("--position-min", type=float, default=4.0)
    p.add_argument("--position-max", type=float, default=20.0)
    p.add_argument("--conversion", type=float, default=0.0,
                   help="taux de conversion, ex. 0.02 pour 2 %%")
    p.add_argument("--panier", type=float, default=0.0, help="valeur moyenne d'une conversion en €")
    p.add_argument("--exporter", default="quick-wins.csv")
    args = p.parse_args()

    lignes = charger(args.csv)
    if not lignes:
        print("Export vide ou illisible.", file=sys.stderr)
        return 1

    cle = "page" if any(l.get("page") for l in lignes) else "requete"
    if not any(l.get(cle) for l in lignes):
        print("Colonne Page ou Requête introuvable dans l'export.", file=sys.stderr)
        return 1

    candidats = [l for l in lignes
                 if args.position_min <= l["position"] <= args.position_max
                 and l["impressions"] >= 100]
    candidats.sort(key=lambda l: l["impressions"], reverse=True)

    resultats = []
    for l in candidats[:40]:
        attendu = ctr_attendu(l["position"])
        cible = 6.0 if l["position"] > 5 else 11.0
        clics_cibles = l["impressions"] * cible / 100
        gain = max(0, clics_cibles - l["clics"])
        euros = gain * args.conversion * args.panier * 12 if args.conversion and args.panier else 0

        if l["ctr"] < attendu * 0.5:
            diagnostic = "CTR faible pour la position — le snippet est en cause, pas le contenu"
            action = "Réécrire title et meta description"
        elif l["position"] > 10:
            diagnostic = "Position 11-20 — contenu insuffisant face au top 3"
            action = "Combler l'écart éditorial + renforcer le maillage interne"
        else:
            diagnostic = "Proche du top 5"
            action = "Enrichir le contenu, ajouter des liens internes"

        resultats.append({
            cle: l.get(cle, ""), "impressions": int(l["impressions"]),
            "clics": int(l["clics"]), "ctr": round(l["ctr"], 2),
            "ctr_attendu": attendu, "position": round(l["position"], 1),
            "gain_clics_mois": int(gain), "gain_euros_an": int(euros),
            "diagnostic": diagnostic, "action": action,
        })

    with open(args.exporter, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(resultats[0].keys()) if resultats else [cle])
        w.writeheader()
        w.writerows(resultats)

    print(f"\n{'═' * 70}")
    print(f"  Quick wins — {len(resultats)} opportunités (positions "
          f"{args.position_min:.0f}-{args.position_max:.0f})")
    print(f"{'═' * 70}\n")

    for r in resultats[:10]:
        print(f"  {r[cle][:62]}")
        print(f"     pos {r['position']:<5} {r['impressions']:>6} impr.  "
              f"{r['clics']:>4} clics  CTR {r['ctr']:.1f} % (attendu {r['ctr_attendu']:.1f} %)")
        print(f"     → +{r['gain_clics_mois']} clics/mois"
              + (f"  ~{r['gain_euros_an']} €/an" if r['gain_euros_an'] else ""))
        print(f"     {r['action']}\n")

    total_gain = sum(r["gain_clics_mois"] for r in resultats[:10])
    print(f"  Potentiel cumulé des 10 premières : +{total_gain} clics/mois")
    if args.conversion and args.panier:
        print(f"  Soit environ {sum(r['gain_euros_an'] for r in resultats[:10]):,} €/an".replace(",", " "))

    # Cannibalisation : plusieurs pages sur la même requête.
    if cle == "page" and any(l.get("requete") for l in lignes):
        par_requete = defaultdict(list)
        for l in lignes:
            if l.get("requete") and l["impressions"] >= 50:
                par_requete[l["requete"]].append(l)
        doublons = {q: v for q, v in par_requete.items() if len({x["page"] for x in v}) > 1}
        if doublons:
            print(f"\n  🟠 {len(doublons)} requête(s) avec plusieurs URL positionnées "
                  "— cannibalisation possible.")

    print(f"\nDétail dans {args.exporter}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
