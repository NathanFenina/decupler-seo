#!/usr/bin/env python3
"""Maillage interne entrant — qui pointe vers une page, avec quelles ancres, et où en ajouter.

    python3 scripts/crawl_site.py https://exemple.com --liens liens.csv --exporter crawl.csv
    python3 scripts/gsc.py perf --par page --jours 90 --lignes 5000 --json > gsc-pages.json
    python3 scripts/maillage_entrant.py --liens liens.csv --pages crawl.csv \\
        --cible https://exemple.com/pompe-a-chaleur/ --mot-cle "pompe à chaleur" \\
        --entites "COP, aides MaPrimeRénov', pompe air-eau" --gsc gsc-pages.json --marque "Exemple" [--json]

Trois réponses, dans l'ordre du livrable :
1. Les liens entrants existants : page source, ancre, zone (contenu, menu,
   en-tête, pied de page, fil d'Ariane), statut de l'ancre, et la diversité
   des ancres (exacte, partielle, marque, générique). Seuls les liens de
   contenu transmettent vraiment de la pertinence : ce sont eux qu'on compte.
2. Les ancres concurrentes : le mot-clé de la page utilisé comme ancre vers
   une AUTRE page. C'est de la cannibalisation par le maillage.
3. Les opportunités, dosées selon la force de la page cible (faible : 4-5
   liens, moyenne : 2-3, forte : 1-2) : les pages sources les plus
   puissantes (clics + impressions Search Console, PageRank interne des
   liens de contenu) et les plus proches du sujet, qui ne lient pas déjà la
   cible. L'ancre exacte n'est proposée qu'une fois, sur la meilleure
   source ; ailleurs, des ancres partielles ou par entité, jamais deux fois
   la même.

Sans dépendance externe.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from urllib.parse import urlparse

AMORTISSEMENT = 0.85
ITERATIONS = 40
ANCRES_GENERIQUES = {"", "ici", "cliquez ici", "en savoir plus", "lire la suite", "voir", "voir plus", "lire",
                     "plus", "suite", "lien", "cet article", "cette page", "découvrir", "decouvrir", "en lire plus"}
MOTS_VIDES = set("le la les l un une des de du d a au aux et ou en pour par sur avec sans dans ce cette ces "
                 "son sa ses votre vos notre nos quel quelle quels quelles comment pourquoi est sont".split())


# ─── Texte ────────────────────────────────────────────────────────

def normaliser_texte(texte: str) -> str:
    t = unicodedata.normalize("NFKD", texte.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", t))


def mots_utiles(texte: str) -> list[str]:
    return [m for m in normaliser_texte(texte).split() if m not in MOTS_VIDES and len(m) > 1]


def normaliser_url(url: str) -> str:
    u = urlparse(url.strip())
    chemin = u.path.rstrip("/") or "/"
    return f"{u.netloc.lower().removeprefix('www.')}{chemin}"


def type_ancre(ancre: str, mot_cle: str, marque: str = "") -> str:
    """exacte · partielle · marque · générique · autre."""
    a = normaliser_texte(ancre)
    if a in {normaliser_texte(g) for g in ANCRES_GENERIQUES}:
        return "générique"
    cle = normaliser_texte(mot_cle)
    if cle and (a == cle or f" {cle} " in f" {a} "):
        return "exacte"
    if marque and normaliser_texte(marque) and normaliser_texte(marque) in a:
        return "marque"
    utiles = set(mots_utiles(mot_cle))
    if utiles and len(utiles & set(mots_utiles(ancre))) * 2 >= len(utiles):
        return "partielle"
    return "autre"


# ─── Graphe ───────────────────────────────────────────────────────

def charger_liens(chemin: str) -> list[dict]:
    with open(chemin, newline="", encoding="utf-8") as f:
        return [{"source": l["source"], "cible": l["cible"], "ancre": l.get("ancre", ""),
                 "zone": l.get("zone", "contenu") or "contenu"} for l in csv.DictReader(f)]


def charger_pages(chemin: str | None) -> dict[str, dict]:
    if not chemin:
        return {}
    with open(chemin, newline="", encoding="utf-8") as f:
        return {normaliser_url(l["url"]): l for l in csv.DictReader(f) if l.get("url")}


def charger_gsc(chemin: str | None) -> dict[str, dict]:
    """JSON de `gsc.py perf --par page --json`, ou CSV page/url, clics/clicks, impressions."""
    if not chemin:
        return {}
    with open(chemin, encoding="utf-8") as f:
        brut = f.read()
    res: dict[str, dict] = {}
    if brut.lstrip().startswith(("{", "[")):
        donnees = json.loads(brut)
        lignes = donnees.get("rows", []) if isinstance(donnees, dict) else donnees
        for r in lignes:
            page = (r.get("keys") or [r.get("page", "")])[0]
            res[normaliser_url(page)] = {"clics": float(r.get("clicks", 0) or 0),
                                         "impressions": float(r.get("impressions", 0) or 0)}
    else:
        for r in csv.DictReader(brut.splitlines()):
            page = r.get("page") or r.get("url") or ""
            res[normaliser_url(page)] = {"clics": float(r.get("clics") or r.get("clicks") or 0),
                                         "impressions": float(r.get("impressions") or 0)}
    return res


def pagerank(liens: list[dict]) -> dict[str, float]:
    """PageRank sur les seuls liens de contenu, une fois par couple source → cible."""
    arcs = {(normaliser_url(l["source"]), normaliser_url(l["cible"])) for l in liens
            if l["zone"] == "contenu" and normaliser_url(l["source"]) != normaliser_url(l["cible"])}
    noeuds = {n for a in arcs for n in a}
    if not noeuds:
        return {}
    sortants = defaultdict(list)
    for s, c in arcs:
        sortants[s].append(c)
    n = len(noeuds)
    pr = dict.fromkeys(noeuds, 1 / n)
    for _ in range(ITERATIONS):
        perdu = sum(pr[x] for x in noeuds if not sortants.get(x))
        nouveau = dict.fromkeys(noeuds, (1 - AMORTISSEMENT) / n + AMORTISSEMENT * perdu / n)
        for s, cibles in sortants.items():
            part = AMORTISSEMENT * pr[s] / len(cibles)
            for c in cibles:
                nouveau[c] += part
        pr = nouveau
    return pr


def rang_percentile(valeurs: dict[str, float], cle: str) -> float:
    """Part des pages dont la valeur est inférieure ou égale : 0 (la plus faible) à 1 (la plus forte)."""
    if not valeurs or cle not in valeurs:
        return 0.0
    v = valeurs[cle]
    return sum(1 for x in valeurs.values() if x <= v) / len(valeurs)


def puissance(url: str, pr: dict[str, float], gsc: dict[str, dict]) -> float:
    """Puissance d'une page source, entre 0 et 1 : moitié PageRank interne, moitié Search Console."""
    p = rang_percentile(pr, url)
    if not gsc:
        return p
    trafic = {u: d["clics"] * 10 + d["impressions"] for u, d in gsc.items()}
    trafic.setdefault(url, 0.0)
    return 0.5 * p + 0.5 * rang_percentile(trafic, url)


def nb_liens_a_ajouter(force_cible: float) -> tuple[int, str]:
    if force_cible < 0.4:
        return 5, "faible"
    if force_cible < 0.75:
        return 3, "moyenne"
    return 2, "forte"


# ─── Analyse ──────────────────────────────────────────────────────

def analyser(liens: list[dict], cible: str, mot_cle: str, entites: list[str] | None = None,
             pages: dict[str, dict] | None = None, gsc: dict[str, dict] | None = None,
             marque: str = "") -> dict:
    pages, gsc, entites = pages or {}, gsc or {}, entites or []
    c = normaliser_url(cible)
    pr = pagerank(liens)

    # 1. Existant
    entrants = [l for l in liens if normaliser_url(l["cible"]) == c and normaliser_url(l["source"]) != c]
    existants = []
    for l in entrants:
        t = type_ancre(l["ancre"], mot_cle, marque)
        statut = ("ancre générique" if t == "générique" else "hors contenu" if l["zone"] != "contenu" else "OK")
        existants.append({**l, "type_ancre": t, "statut": statut})
    sources_contenu = {normaliser_url(l["source"]) for l in entrants if l["zone"] == "contenu"}
    diversite = Counter(e["type_ancre"] for e in existants if e["zone"] == "contenu")

    # 2. Ancres concurrentes : le mot-clé envoyé ailleurs
    concurrentes = [{**l, "type_ancre": "exacte"} for l in liens
                    if normaliser_url(l["cible"]) != c and l["zone"] == "contenu"
                    and type_ancre(l["ancre"], mot_cle, marque) == "exacte"]

    # 3. Opportunités
    deja = {normaliser_url(l["source"]) for l in entrants}
    sujet = set(mots_utiles(mot_cle)) | {m for e in entites for m in mots_utiles(e)}
    candidats = []
    for url in set(pr) | set(pages) | set(gsc):
        if url == c or url in deja:
            continue
        info = pages.get(url, {})
        if info and (str(info.get("indexable", "True")) == "False" or str(info.get("statut", "200")) not in ("200", "")):
            continue
        texte = " ".join([info.get("title", ""), info.get("h1", ""), url.replace("-", " ").replace("/", " ")])
        proximite = len(sujet & set(mots_utiles(texte))) / len(sujet) if sujet else 0.0
        force = puissance(url, pr, gsc)
        candidats.append({"source": url, "puissance": round(force, 2), "proximite": round(proximite, 2),
                          "score": round(0.55 * force + 0.45 * proximite, 3),
                          "clics": gsc.get(url, {}).get("clics", 0),
                          "impressions": gsc.get(url, {}).get("impressions", 0),
                          "title": info.get("title", "")})
    candidats.sort(key=lambda x: -x["score"])

    force_cible = puissance(c, pr, gsc) if (pr or gsc) else 0.0
    nombre, niveau = nb_liens_a_ajouter(force_cible)
    retenus = [x for x in candidats if x["proximite"] > 0 or x["puissance"] >= 0.8][:nombre]

    # Ancres : l'exacte une seule fois (et seulement si aucun lien de contenu ne la porte déjà),
    # puis partielles et entités, jamais deux fois la même.
    deja_exacte = diversite.get("exacte", 0) > 0
    propositions = ([] if deja_exacte else [mot_cle]) + entites + [f"{e} et {mot_cle}" for e in entites[:2]]
    vues = {normaliser_texte(e["ancre"]) for e in existants if e["zone"] == "contenu"}
    file = [a for a in dict.fromkeys(propositions) if normaliser_texte(a) not in vues]
    for i, x in enumerate(retenus):
        x["ancre"] = file[i] if i < len(file) else f"[ancre par entité liée à « {mot_cle} »]"
        x["priorite"] = "haute" if i == 0 else "moyenne" if i < 3 else "basse"
    # Une ancre concurrente redirigée vers la cible ferait une 2e ancre exacte : on la change.
    porteur = next((x["source"] for x in retenus if x["ancre"] == mot_cle), None)
    for e in concurrentes:
        e["consigne"] = (f"changer l'ancre, sans la rediriger vers la cible : l'ancre exacte va sur {porteur}"
                         if porteur else "changer l'ancre (la cible porte déjà l'ancre exacte) ou retirer le lien")

    return {"cible": cible, "mot_cle": mot_cle,
            "force_cible": round(force_cible, 2), "niveau": niveau, "liens_a_ajouter": nombre,
            "existants": existants, "sources_contenu": len(sources_contenu),
            "diversite_ancres": dict(diversite), "ancres_concurrentes": concurrentes,
            "opportunites": retenus}


def afficher(r: dict) -> None:
    print(f"\n  Maillage entrant de {r['cible']}  ·  mot-clé « {r['mot_cle']} »")
    print(f"  Force de la page : {r['niveau']} ({r['force_cible']}) → {r['liens_a_ajouter']} lien(s) à ajouter\n")
    print(f"─── 1. Liens entrants existants : {len(r['existants'])} "
          f"(dont {r['sources_contenu']} page(s) source en contenu) ───")
    for e in r["existants"]:
        print(f"  {e['statut']:<16} {e['zone']:<14} « {e['ancre'][:60]} » ({e['type_ancre']})  ← {e['source']}")
    if r["diversite_ancres"]:
        print("  Diversité des ancres (contenu) : "
              + ", ".join(f"{k} {v}" for k, v in sorted(r["diversite_ancres"].items())))
    print(f"\n─── 2. Ancres concurrentes : {len(r['ancres_concurrentes'])} ───")
    for e in r["ancres_concurrentes"]:
        print(f"  « {e['ancre'][:60]} »  {e['source']} → {e['cible']}\n    → {e['consigne']}")
    print(f"\n─── 3. Opportunités ({len(r['opportunites'])}) ───")
    for x in r["opportunites"]:
        trafic = f"{x['clics']:.0f} clics / {x['impressions']:.0f} impr." if x["clics"] or x["impressions"] else "—"
        print(f"  [{x['priorite']}] {x['source']}  ancre « {x['ancre']} »  "
              f"(puissance {x['puissance']}, proximité {x['proximite']}, GSC {trafic})")
    print("\n  Pour chaque opportunité : trouver la phrase existante où placer le lien, "
          "ou en écrire une, et l'intégrer au livrable.\n")


def main() -> int:
    p = argparse.ArgumentParser(description="Maillage interne entrant d'une page")
    p.add_argument("--liens", required=True, help="CSV de crawl_site.py --liens")
    p.add_argument("--pages", help="CSV de crawl_site.py --exporter (title, H1, indexabilité)")
    p.add_argument("--cible", required=True, help="URL de la page à renforcer")
    p.add_argument("--mot-cle", required=True)
    p.add_argument("--entites", default="", help="entités liées, séparées par des virgules (ancres partielles)")
    p.add_argument("--gsc", help="JSON de gsc.py perf --par page --json, ou CSV page/clics/impressions")
    p.add_argument("--marque", default="", help="nom de la marque, pour classer les ancres de marque")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    entites = [e.strip() for e in a.entites.split(",") if e.strip()]
    r = analyser(charger_liens(a.liens), a.cible, a.mot_cle, entites,
                 charger_pages(a.pages), charger_gsc(a.gsc), a.marque)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        afficher(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
