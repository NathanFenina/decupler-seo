#!/usr/bin/env python3
"""Share of Model — mesure la part de voix d'une marque dans les moteurs IA.

    python3 scripts/share_of_model.py --prompts prompts.csv --marque "Décupler"
    python3 scripts/share_of_model.py --gabarit          # crée un prompts.csv d'exemple

Interroge Perplexity via son API si PERPLEXITY_API_KEY est présente. Sans
clé, le script prépare la grille de relevé à remplir manuellement — la
mesure reste possible, elle est juste plus lente.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import charger_env  # noqa: E402

# Une 1re citation vaut plus qu'une 4e : le poids reflète ce qu'un lecteur
# retient réellement d'une réponse générée.
POIDS_RANG = {1: 1.0, 2: 0.6, 3: 0.4}
POIDS_DEFAUT = 0.2

GABARIT = [
    ("decouverte", "Quels sont les meilleurs {categorie} en France ?"),
    ("decouverte", "Comment choisir un {categorie} ?"),
    ("comparaison", "{concurrent} ou {marque}, lequel choisir ?"),
    ("comparaison", "Quelle alternative à {concurrent} ?"),
    ("probleme", "Comment résoudre {probleme} ?"),
    ("probleme", "Combien coûte {service} ?"),
    ("marque", "Que vaut {marque} ?"),
    ("marque", "Quels sont les avis sur {marque} ?"),
]



def ecrire_gabarit(chemin: str) -> int:
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["famille", "prompt"])
        w.writerows(GABARIT)
    print(f"\n  Gabarit écrit dans {chemin}.\n")
    print("  Remplacez les variables entre accolades par vos termes réels,")
    print("  puis complétez jusqu'à 20-40 prompts. Répartition conseillée :")
    print("  30 % découverte · 25 % comparaison · 25 % problème · 20 % marque.\n")
    print("  ⚠️  Une fois la liste établie, ne la modifiez plus : la")
    print("  comparaison d'un mois sur l'autre n'a de sens qu'à liste figée.\n")
    return 0


def interroger_perplexity(prompt: str, cle: str) -> dict:
    import requests
    rep = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers={"Authorization": f"Bearer {cle}", "Content-Type": "application/json"},
        json={"model": "sonar", "messages": [{"role": "user", "content": prompt}]},
        timeout=60)
    rep.raise_for_status()
    donnees = rep.json()
    texte = donnees["choices"][0]["message"]["content"]
    citations = donnees.get("citations", []) or donnees.get("search_results", [])
    domaines = []
    for c in citations:
        url = c if isinstance(c, str) else c.get("url", "")
        found = re.search(r"https?://(?:www\.)?([^/]+)", url)
        if found:
            domaines.append(found.group(1).lower())
    return {"texte": texte, "domaines": domaines}


def analyser(reponse: dict, marque: str, domaine: str) -> dict:
    domaines = reponse["domaines"]
    texte_bas = reponse["texte"].lower()

    rang = 0
    for i, d in enumerate(domaines, 1):
        if domaine and domaine.lower().removeprefix("www.") in d:
            rang = i
            break

    mentionne_texte = marque.lower() in texte_bas
    return {
        "cite": rang > 0,
        "rang": rang,
        "mention_texte": mentionne_texte,
        "domaines_cites": ", ".join(domaines[:6]),
        "extrait": next((p.strip() for p in re.split(r"(?<=[.!?])\s", reponse["texte"])
                         if marque.lower() in p.lower()), "")[:250],
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Share of Model")
    p.add_argument("--prompts", default="prompts.csv")
    p.add_argument("--marque", default="")
    p.add_argument("--domaine", default="", help="votre domaine, ex. exemple.com")
    p.add_argument("--gabarit", action="store_true", help="écrit un prompts.csv d'exemple")
    p.add_argument("--exporter", default="")
    args = p.parse_args()

    if args.gabarit:
        return ecrire_gabarit(args.prompts)

    chemin = Path(args.prompts)
    if not chemin.exists():
        print(f"\n  Fichier de prompts introuvable : {args.prompts}")
        print("  Créez-en un avec : python3 scripts/share_of_model.py --gabarit\n")
        return 1

    charger_env()
    cle = os.environ.get("PERPLEXITY_API_KEY", "").strip()
    domaine = args.domaine or os.environ.get("GSC_SITE_URL", "").replace("https://", "").strip("/")

    with open(chemin, newline="", encoding="utf-8") as f:
        prompts = [l for l in csv.DictReader(f) if l.get("prompt")]

    sortie = args.exporter or f"releves-{date.today():%Y-%m}.csv"

    if not cle:
        print("\n  PERPLEXITY_API_KEY absente — grille de relevé manuel préparée.\n")
        print("  Posez chaque prompt en session neuve, sans historique, dans la")
        print("  bonne langue et le bon pays, puis remplissez les colonnes.\n")
        with open(sortie, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["famille", "prompt", "moteur", "cite_oui_non", "rang",
                        "domaines_cites", "extrait", "exactitude"])
            for l in prompts:
                for moteur in ("ChatGPT", "Perplexity", "AI Overview", "Claude", "Gemini"):
                    w.writerow([l.get("famille", ""), l["prompt"], moteur, "", "", "", "", ""])
        print(f"  Grille écrite dans {sortie}\n")
        return 0

    print(f"\n  Interrogation de Perplexity sur {len(prompts)} prompts…\n")
    releves, cites, poids_total, poids_marque = [], 0, 0.0, 0.0

    for i, ligne in enumerate(prompts, 1):
        prompt = ligne["prompt"]
        try:
            reponse = interroger_perplexity(prompt, cle)
        except Exception as exc:
            print(f"  [{i:>2}] ✗ {prompt[:50]} — {str(exc)[:60]}")
            continue

        res = analyser(reponse, args.marque, domaine)
        nb_sources = max(1, len(reponse["domaines"]))
        poids_total += sum(POIDS_RANG.get(r, POIDS_DEFAUT) for r in range(1, nb_sources + 1))
        if res["cite"]:
            cites += 1
            poids_marque += POIDS_RANG.get(res["rang"], POIDS_DEFAUT)

        marque_etat = f"✓ rang {res['rang']}" if res["cite"] else "✗"
        print(f"  [{i:>2}] {marque_etat:<12} {prompt[:52]}")

        releves.append({"famille": ligne.get("famille", ""), "prompt": prompt,
                        "moteur": "Perplexity", **res})

    with open(sortie, "w", newline="", encoding="utf-8") as f:
        if releves:
            w = csv.DictWriter(f, fieldnames=list(releves[0].keys()))
            w.writeheader()
            w.writerows(releves)

    n = len(releves) or 1
    taux = cites / n * 100
    som = poids_marque / poids_total * 100 if poids_total else 0

    print(f"\n{'═' * 56}")
    print(f"  Taux de citation   {cites}/{n}  =  {taux:.1f} %")
    print(f"  Share of model pondéré           {som:.1f} %")
    print(f"{'═' * 56}\n")

    if taux < 10:
        print("  🔴 Quasi invisible. Le problème est l'autorité externe, pas le")
        print("     contenu du site. Voir /seo reddit et /seo pr.\n")
    elif taux < 30:
        print("  🟠 Présence naissante. Travaillez la citabilité des pages")
        print("     principales — voir /seo citation.\n")
    else:
        print("  🟢 Position solide. Maintenez et étendez à de nouveaux prompts.\n")

    print(f"  Relevés dans {sortie}. Refaites la mesure dans un mois, même liste.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
