#!/usr/bin/env python3
"""Analyse des redirections — chaînes, boucles, 302 déguisées, 404.

    python3 scripts/check_redirects.py https://exemple.com/page
    python3 scripts/check_redirects.py urls.txt --exporter redirections.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Dépendance manquante : pip install -r requirements.txt", file=sys.stderr)
    raise SystemExit(1)

AGENT = "ClaudeCodeSEODecupler/2.0 (+https://decupler.com)"
MAX_SAUTS = 10


def suivre(url: str) -> dict:
    """Suit la chaîne de redirection saut par saut."""
    chaine, vues = [], set()
    courante = url

    for _ in range(MAX_SAUTS):
        if courante in vues:
            return {"url": url, "sauts": len(chaine), "chaine": chaine,
                    "final": courante, "statut_final": 0,
                    "probleme": "boucle de redirection", "gravite": "critique"}
        vues.add(courante)

        try:
            rep = requests.head(courante, headers={"User-Agent": AGENT},
                                allow_redirects=False, timeout=20)
            # Certains serveurs refusent HEAD : on retente en GET.
            if rep.status_code in (405, 501):
                rep = requests.get(courante, headers={"User-Agent": AGENT},
                                   allow_redirects=False, timeout=20, stream=True)
        except requests.RequestException as exc:
            return {"url": url, "sauts": len(chaine), "chaine": chaine,
                    "final": courante, "statut_final": 0,
                    "probleme": f"inaccessible : {exc}"[:120], "gravite": "critique"}

        if 300 <= rep.status_code < 400 and "Location" in rep.headers:
            suivant = requests.compat.urljoin(courante, rep.headers["Location"])
            chaine.append({"de": courante, "vers": suivant, "statut": rep.status_code})
            courante = suivant
            continue

        # Fin de chaîne : on qualifie.
        probleme, gravite = "", "ok"
        if rep.status_code >= 500:
            probleme, gravite = f"erreur serveur {rep.status_code}", "critique"
        elif rep.status_code == 404:
            probleme, gravite = "404 en fin de chaîne", "critique"
        elif rep.status_code >= 400:
            probleme, gravite = f"erreur {rep.status_code}", "fort"
        elif len(chaine) > 2:
            probleme, gravite = f"chaîne de {len(chaine)} sauts — à aplatir", "fort"
        elif any(s["statut"] == 302 for s in chaine):
            probleme, gravite = "302 utilisée pour une redirection permanente — passer en 301", "fort"
        elif len(chaine) == 2:
            probleme, gravite = "2 sauts — aplatir vers la destination finale", "moyen"

        return {"url": url, "sauts": len(chaine), "chaine": chaine,
                "final": courante, "statut_final": rep.status_code,
                "probleme": probleme, "gravite": gravite}

    return {"url": url, "sauts": MAX_SAUTS, "chaine": chaine, "final": courante,
            "statut_final": 0, "probleme": f"plus de {MAX_SAUTS} sauts", "gravite": "critique"}


def main() -> int:
    p = argparse.ArgumentParser(description="Analyse des redirections")
    p.add_argument("source", help="une URL, ou un fichier texte avec une URL par ligne")
    p.add_argument("--exporter", default="redirections.csv")
    args = p.parse_args()

    chemin = Path(args.source)
    urls = ([u.strip() for u in chemin.read_text(encoding="utf-8").splitlines() if u.strip()]
            if chemin.exists() else [args.source])

    resultats = []
    for url in urls:
        res = suivre(url)
        resultats.append(res)
        icone = {"ok": "🟢", "moyen": "🟡", "fort": "🟠", "critique": "🔴"}[res["gravite"]]
        print(f"{icone} {url}")
        for saut in res["chaine"]:
            print(f"     {saut['statut']} → {saut['vers']}")
        if res["probleme"]:
            print(f"     ⚠️  {res['probleme']}")
        print()

    with open(args.exporter, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["url", "sauts", "url_finale", "statut_final", "probleme", "gravite"])
        for r in resultats:
            w.writerow([r["url"], r["sauts"], r["final"], r["statut_final"],
                        r["probleme"], r["gravite"]])

    critiques = [r for r in resultats if r["gravite"] == "critique"]
    if critiques:
        print(f"🔴 {len(critiques)} problème(s) critique(s).")
        print("   Une 404 qui reçoit des backlinks est la perte la plus silencieuse")
        print("   du SEO. Redirigez en 301 vers l'équivalent le plus proche —")
        print("   jamais vers la home, Google traite cela comme un soft 404.\n")

    print(f"Détail dans {args.exporter}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
