#!/usr/bin/env python3
"""Share of Model — la part de voix d'une marque dans les moteurs IA.

    python3 share_of_model.py --gabarit                   # crée prompts.csv
    python3 share_of_model.py --prompts prompts.csv       # tous les moteurs disponibles
    python3 share_of_model.py --moteurs openai,gemini --marque "Tasis" --domaine tasispartners.com

Chaque moteur est interrogé avec sa recherche web activée — c'est ce que voit
un utilisateur, et c'est la seule façon de relever les sources citées :

    openai      OPENAI_API_KEY      Responses API + web_search  (ChatGPT)
    gemini      GEMINI_API_KEY      generateContent + google_search (Gemini, proche d'AI Overviews)
    claude      ANTHROPIC_API_KEY   Messages API + web_search
    perplexity  PERPLEXITY_API_KEY  Sonar

Un moteur sans clé est simplement ignoré. Sans aucune clé, le script prépare
la grille de relevé manuel. Modèles réglables : SOM_MODELE_OPENAI,
SOM_MODELE_GEMINI, SOM_MODELE_CLAUDE, SOM_MODELE_PERPLEXITY.

Deux mesures distinctes, qui ne se lisent pas ensemble :
- **visibilité** : sur les prompts sans le nom de la marque (découverte,
  comparaison, problème), la marque est-elle citée ou nommée ?
- **réputation** : sur les prompts de la famille « marque », ce qui est dit.

Sans dépendance.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import charger_env, lire_valeur  # noqa: E402

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


class ErreurMoteur(RuntimeError):
    pass


def _post(url: str, corps: dict, entetes: dict, timeout: int = 120) -> dict:
    requete = urllib.request.Request(url, data=json.dumps(corps).encode(), method="POST",
                                     headers={"Content-Type": "application/json", **entetes})
    try:
        with urllib.request.urlopen(requete, timeout=timeout) as rep:
            return json.loads(rep.read())
    except urllib.error.HTTPError as exc:
        # Le corps d'erreur ne contient jamais la clé ; on le tronque quand même.
        raise ErreurMoteur(f"HTTP {exc.code} {exc.read()[:160].decode('utf-8', 'replace')}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ErreurMoteur(str(exc)[:160]) from None


def domaine_de(url: str) -> str:
    hote = urllib.parse.urlparse(url).netloc.lower()
    return hote.removeprefix("www.")


# ─── Moteurs ──────────────────────────────────────────────────────
# Chacun renvoie {"texte": str, "sources": [domaine, …]} dans l'ordre de citation.

def openai(prompt: str) -> dict:
    d = _post("https://api.openai.com/v1/responses",
              {"model": os.environ.get("SOM_MODELE_OPENAI", "gpt-5-mini"),
               "tools": [{"type": "web_search"}], "input": prompt},
              {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"})
    texte, sources = [], []
    for element in d.get("output", []):
        for contenu in element.get("content", []) or []:
            if contenu.get("type") == "output_text":
                texte.append(contenu.get("text", ""))
                sources += [domaine_de(a["url"]) for a in contenu.get("annotations", [])
                            if a.get("type") == "url_citation" and a.get("url")]
    return {"texte": "\n".join(texte), "sources": sources}


def gemini(prompt: str) -> dict:
    modele = os.environ.get("SOM_MODELE_GEMINI", "gemini-2.5-flash")
    d = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{modele}:generateContent",
              {"contents": [{"parts": [{"text": prompt}]}], "tools": [{"google_search": {}}]},
              {"x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    candidat = (d.get("candidates") or [{}])[0]
    texte = "".join(p.get("text", "") for p in candidat.get("content", {}).get("parts", []))
    sources = []
    for morceau in candidat.get("groundingMetadata", {}).get("groundingChunks", []):
        web = morceau.get("web", {})
        # L'URI est une redirection Google ; le titre porte le domaine de la source.
        titre = (web.get("title") or "").lower().removeprefix("www.")
        sources.append(titre if "." in titre and " " not in titre else domaine_de(web.get("uri", "")))
    return {"texte": texte, "sources": sources}


def claude(prompt: str) -> dict:
    d = _post("https://api.anthropic.com/v1/messages",
              {"model": os.environ.get("SOM_MODELE_CLAUDE", "claude-sonnet-5-5"), "max_tokens": 2048,
               "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
               "messages": [{"role": "user", "content": prompt}]},
              {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"})
    texte, sources = [], []
    for bloc in d.get("content", []):
        if bloc.get("type") == "text":
            texte.append(bloc.get("text", ""))
            sources += [domaine_de(c["url"]) for c in bloc.get("citations", []) or [] if c.get("url")]
    return {"texte": "".join(texte), "sources": sources}


def perplexity(prompt: str) -> dict:
    d = _post("https://api.perplexity.ai/chat/completions",
              {"model": os.environ.get("SOM_MODELE_PERPLEXITY", "sonar"),
               "messages": [{"role": "user", "content": prompt}]},
              {"Authorization": f"Bearer {os.environ['PERPLEXITY_API_KEY']}"})
    citations = d.get("citations") or [r.get("url", "") for r in d.get("search_results", [])]
    return {"texte": d["choices"][0]["message"]["content"],
            "sources": [domaine_de(c if isinstance(c, str) else c.get("url", "")) for c in citations]}


MOTEURS = {"openai": ("OPENAI_API_KEY", openai), "gemini": ("GEMINI_API_KEY", gemini),
           "claude": ("ANTHROPIC_API_KEY", claude), "perplexity": ("PERPLEXITY_API_KEY", perplexity)}


def moteurs_disponibles(demandes: list[str] | None = None) -> list[str]:
    noms = demandes or list(MOTEURS)
    return [n for n in noms if n in MOTEURS and os.environ.get(MOTEURS[n][0], "").strip()]


# ─── Analyse ──────────────────────────────────────────────────────

def sans_doublons(sources: list[str]) -> list[str]:
    vus, ordre = set(), []
    for s in sources:
        if s and s not in vus:
            vus.add(s)
            ordre.append(s)
    return ordre


def analyser(reponse: dict, marque: str, domaine: str) -> dict:
    sources = sans_doublons(reponse["sources"])
    domaine = domaine.lower().removeprefix("www.")
    rang = next((i for i, s in enumerate(sources, 1) if domaine and (s == domaine or s.endswith("." + domaine))), 0)
    texte = reponse["texte"]
    nomme = bool(marque) and marque.lower() in texte.lower()
    return {
        "cite": rang > 0, "rang": rang, "nomme": nomme,
        "sources": ", ".join(sources[:8]),
        "extrait": next((p.strip() for p in re.split(r"(?<=[.!?])\s", texte)
                         if marque and marque.lower() in p.lower()), "")[:250],
    }


def synthese(releves: list[dict]) -> dict:
    """Par moteur : visibilité (prompts non marqués) et part de voix pondérée."""
    par_moteur: dict[str, dict] = {}
    for r in releves:
        m = par_moteur.setdefault(r["moteur"], {"prompts": 0, "cites": 0, "nommes": 0,
                                                 "poids_marque": 0.0, "poids_total": 0.0, "reputation": 0})
        if r["famille"] == "marque":
            m["reputation"] += 1
            continue
        m["prompts"] += 1
        m["cites"] += r["cite"]
        m["nommes"] += r["nomme"]
        nb = max(1, len([s for s in r["sources"].split(", ") if s]))
        m["poids_total"] += sum(POIDS_RANG.get(i, POIDS_DEFAUT) for i in range(1, nb + 1))
        if r["cite"]:
            m["poids_marque"] += POIDS_RANG.get(r["rang"], POIDS_DEFAUT)
    for m in par_moteur.values():
        n = m["prompts"] or 1
        m["taux_citation_pct"] = round(m["cites"] / n * 100, 1)
        m["taux_mention_pct"] = round(m["nommes"] / n * 100, 1)
        m["share_of_model_pct"] = round(m["poids_marque"] / m["poids_total"] * 100, 1) if m["poids_total"] else 0.0
    return par_moteur


def domaines_concurrents(releves: list[dict], domaine: str, n: int = 10) -> list[tuple[str, int]]:
    compte: dict[str, int] = {}
    for r in releves:
        if r["famille"] == "marque":
            continue
        for s in set(filter(None, r["sources"].split(", "))):
            if not (domaine and s.endswith(domaine)):
                compte[s] = compte.get(s, 0) + 1
    return sorted(compte.items(), key=lambda x: -x[1])[:n]


# ─── Commandes ────────────────────────────────────────────────────

def ecrire_gabarit(chemin: str) -> int:
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["famille", "prompt"])
        w.writerows(GABARIT)
    print(f"\n  Gabarit écrit dans {chemin}.\n")
    print("  Remplacez les variables entre accolades par vos termes réels, puis")
    print("  complétez jusqu'à 20-40 prompts, trois formulations par sujet :")
    print("  30 % découverte · 25 % comparaison · 25 % problème · 20 % marque.\n")
    print("  ⚠️  Une fois la liste établie, ne la modifiez plus : la comparaison")
    print("  d'un mois sur l'autre n'a de sens qu'à liste figée.\n")
    return 0


def grille_manuelle(prompts: list[dict], sortie: str) -> int:
    print("\n  Aucune clé de moteur IA — grille de relevé manuel préparée.")
    print("  Posez chaque prompt en session neuve, sans historique, dans la bonne")
    print("  langue et le bon pays, puis remplissez les colonnes.\n")
    with open(sortie, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["famille", "prompt", "moteur", "cite", "rang", "nomme", "sources", "extrait", "exactitude"])
        for l in prompts:
            for moteur in ("ChatGPT", "Gemini", "AI Overview", "Claude", "Perplexity"):
                w.writerow([l.get("famille", ""), l["prompt"], moteur, "", "", "", "", "", ""])
    print(f"  Grille écrite dans {sortie}\n")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Share of Model — part de voix dans les moteurs IA")
    p.add_argument("--prompts", default="prompts.csv")
    p.add_argument("--marque", default="", help="défaut : projet.nom de la config")
    p.add_argument("--domaine", default="", help="défaut : projet.domaine de la config")
    p.add_argument("--moteurs", default="", help="ex. openai,gemini (défaut : tous ceux qui ont une clé)")
    p.add_argument("--gabarit", action="store_true", help="écrit un prompts.csv d'exemple")
    p.add_argument("--exporter", default="")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    if args.gabarit:
        return ecrire_gabarit(args.prompts)

    chemin = Path(args.prompts)
    if not chemin.exists():
        print(f"\n  Fichier de prompts introuvable : {args.prompts}")
        print("  Créez-en un avec : share_of_model.py --gabarit\n")
        return 1

    charger_env()
    marque = args.marque or lire_valeur("projet.nom")
    domaine = domaine_de(args.domaine if "//" in args.domaine else f"https://{args.domaine}") if args.domaine \
        else domaine_de(lire_valeur("projet.domaine"))
    with open(chemin, newline="", encoding="utf-8") as f:
        prompts = [l for l in csv.DictReader(f) if l.get("prompt")]
    sortie = args.exporter or f"releves-ia-{date.today():%Y-%m}.csv"

    moteurs = moteurs_disponibles([m.strip() for m in args.moteurs.split(",") if m.strip()] or None)
    if not moteurs:
        return grille_manuelle(prompts, sortie)

    if not args.json:
        print(f"\n  {len(prompts)} prompts × {', '.join(moteurs)} · marque « {marque} » · {domaine}\n")
    releves, erreurs = [], 0
    for moteur in moteurs:
        fonction = MOTEURS[moteur][1]
        for i, ligne in enumerate(prompts, 1):
            try:
                reponse = fonction(ligne["prompt"])
            except (ErreurMoteur, KeyError, IndexError) as exc:
                erreurs += 1
                if not args.json:
                    print(f"  {moteur:<10} [{i:>2}] ✗ {str(exc)[:90]}")
                continue
            res = analyser(reponse, marque, domaine)
            releves.append({"moteur": moteur, "famille": ligne.get("famille", ""), "prompt": ligne["prompt"], **res})
            if not args.json:
                etat = f"cité rang {res['rang']}" if res["cite"] else ("nommé" if res["nomme"] else "absent")
                print(f"  {moteur:<10} [{i:>2}] {etat:<14} {ligne['prompt'][:60]}")
            time.sleep(0.5)

    if releves:
        with open(sortie, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(releves[0].keys()))
            w.writeheader()
            w.writerows(releves)

    bilan = synthese(releves)
    concurrents = domaines_concurrents(releves, domaine)
    if args.json:
        print(json.dumps({"marque": marque, "domaine": domaine, "moteurs": bilan, "erreurs": erreurs,
                          "sources_les_plus_citees": concurrents, "releves": sortie}, ensure_ascii=False, indent=1))
        return 0 if releves else 1

    print(f"\n  {'Moteur':<11}{'citation':>10}{'mention':>10}{'part de voix':>14}   (prompts sans la marque)")
    for moteur, m in bilan.items():
        print(f"  {moteur:<11}{m['taux_citation_pct']:>9.1f}%{m['taux_mention_pct']:>9.1f}%{m['share_of_model_pct']:>13.1f}%")
    if concurrents:
        print("\n  Sources les plus citées à votre place :")
        for s, n in concurrents:
            print(f"    {n:>3} × {s}")
    print(f"\n  Relevés complets dans {sortie} — la réputation (famille « marque ») s'y lit prompt par prompt.")
    print("  Refaites la mesure dans un mois, avec la même liste.\n")
    return 0 if releves else 1


if __name__ == "__main__":
    sys.exit(main())
