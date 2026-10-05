#!/usr/bin/env python3
"""La SERP d'un mot-clé, lue page par page : la matière mesurée du brief.

    python3 serp_concurrents.py --mot "pompe à chaleur air eau" --langue fr
    python3 serp_concurrents.py --mot "expert comptable lyon" --url https://www.exemple.fr/expert-comptable-lyon/
    python3 serp_concurrents.py --mot "…" --top 8 --repli-dataforseo --json

1. SERP Google en direct (DataForSEO, top 10 organique, « Autres questions
   posées » dépliées d'un niveau, AI Overview chargé même asynchrone,
   recherches associées, features).
2. Lecture des N premières pages concurrentes (5 par défaut, la page du
   client exclue) : title, meta, plan H1-H3, listes, tableaux, mots, FAQ,
   schémas, images, liens, dates, ton (vous / tu, nous / je, longueur des
   phrases). Une page qui ne se lit pas est notée et sautée ; avec
   --repli-dataforseo, elle est relue par DataForSEO (on_page/content_parsing,
   JavaScript exécuté — payant, coût affiché).
3. Agrégation : longueur médiane et 3e quartile (la fourchette cible),
   sujets de H2 récurrents d'une page à l'autre, questions PAA et celles que
   le top ne traite dans aucun titre, sources citées par l'AI Overview,
   termes présents sur au moins la moitié du top.
4. Avec --url (ou projet.domaine) : la page du client lue de la même façon,
   et ce qui lui manque face au top — sujets, termes, questions, longueur.

Sans DataForSEO (repli documenté dans `seo-brief`) : la SERP vient d'une
recherche Firecrawl enregistrée (--serp-firecrawl, top organique seulement :
ni PAA ni AI Overview, notés « non mesurés »), les questions d'un fichier
(--questions : PAA relevées à la main, Ubersuggest, Search Console) et les
pages d'un relevé Firecrawl déjà fait (--pages-json : url + html ou
markdown). Avec --sitemap, les pages du site du client les plus proches du
sujet sortent comme candidates au maillage interne.

    python3 serp_concurrents.py --mot "audit geo" --serp-firecrawl serp.json \
        --pages-json pages.json --questions paa.txt --sitemap https://exemple.fr/sitemap.xml

Écrit recherche/serp-<slug>-<date>.md (le rapport) et
recherche/serp-<slug>-<date>-contenus.md (le contenu structuré de chaque
concurrent, titres et listes conservés, à lire avant d'écrire le brief).
--json imprime le rapport complet sur la sortie standard.

Coût : ~0,002 $ la SERP (+0,002 $ si un AI Overview asynchrone est chargé,
+0,00015 $ par question dépliée). La lecture des pages est gratuite ; le
repli DataForSEO est facturé à la page. Sans dépendance.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _contenu as C  # noqa: E402
import demande  # noqa: E402
from _projet import charger_env, lire_valeur, racine_projet  # noqa: E402

MOTS_MINI = 200          # en dessous, la page est mal lue (bloquée, rendue en JS) : hors statistiques
BUDGET_CONTENU = 12_000  # caractères de contenu structuré conservés par concurrent

TITRES_GENERIQUES = re.compile(
    r"^(?:faq|questions? frequentes?|foire aux questions|sommaire|table des matieres|conclusion|en conclusion|"
    r"introduction|en resume|a retenir|pour aller plus loin|a lire aussi|lire aussi|articles? (?:similaires|lies|"
    r"recents|populaires)|nos derniers articles|partager(?: cet article)?|commentaires?|laisser un commentaire|"
    r"newsletter|contact(?:ez-nous)?|a propos(?: de l'auteur)?|l'auteur|sources?|references?|mentions legales)\W*$")


# ─── SERP ─────────────────────────────────────────────────────────

def domaine(url: str) -> str:
    h = (urlparse(url or "").hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def _references(objet) -> list[dict]:
    refs = []
    if isinstance(objet, dict):
        for r in objet.get("references") or []:
            if isinstance(r, dict) and r.get("url"):
                refs.append({"domaine": domaine(r["url"]) or r.get("domain"), "url": r["url"],
                             "titre": r.get("title") or r.get("source") or ""})
        for v in objet.get("items") or []:
            refs += _references(v)
    return refs


def lire_serp(resultats: list[dict]) -> dict:
    """La réponse de serp/google/organic/live/advanced, réduite à ce que le brief utilise."""
    organique, questions, associees, features = [], [], [], set()
    aio = {"present": False, "sources": [], "extrait": ""}
    extrait_position0 = None
    for r in resultats or []:
        features.update(r.get("item_types") or [])
        for it in r.get("items") or []:
            t = it.get("type")
            if t == "organic":
                organique.append({"rang": it.get("rank_group"), "url": it.get("url"),
                                  "domaine": domaine(it.get("url")) or it.get("domain"),
                                  "titre": it.get("title") or "", "description": it.get("description") or ""})
            elif t == "people_also_ask":
                questions += [q.get("title") for q in it.get("items") or [] if q.get("title")]
            elif t in ("related_searches", "people_also_search"):
                associees += [x if isinstance(x, str) else x.get("title", "") for x in it.get("items") or []]
            elif t == "ai_overview":
                aio["present"] = True
                aio["sources"] += _references(it)
                texte = it.get("markdown") or " ".join(x.get("markdown") or x.get("text") or ""
                                                       for x in it.get("items") or [] if isinstance(x, dict))
                aio["extrait"] = aio["extrait"] or re.sub(r"\s+", " ", texte).strip()[:900]
            elif t == "featured_snippet" and not extrait_position0:
                extrait_position0 = {"url": it.get("url"), "domaine": domaine(it.get("url")) or it.get("domain"),
                                     "titre": it.get("title") or "", "description": it.get("description") or ""}
    vus, sources = set(), []
    for s in aio["sources"]:
        if s["url"] not in vus:
            vus.add(s["url"])
            sources.append(s)
    aio["sources"] = sources
    aio["mesure"] = True
    return {"source": "DataForSEO", "organique": organique, "questions": list(dict.fromkeys(questions)),
            "recherches_associees": [a for a in dict.fromkeys(associees) if a],
            "ai_overview": aio, "extrait_optimise": extrait_position0, "features": sorted(features)}


def lire_serp_firecrawl(brut) -> dict:
    """Une recherche Firecrawl (firecrawl_search, MCP ou API) réduite au même format que lire_serp.

    Firecrawl ne renvoie que le classement organique : PAA, AI Overview, extrait optimisé et features
    restent « non mesurés » (et non « absents ») — le rapport le dit, le brief les relève autrement.
    """
    if isinstance(brut, dict):
        brut = (brut.get("data") or brut)
        brut = brut.get("web") or brut.get("results") or [] if isinstance(brut, dict) else brut
    organique = []
    for i, it in enumerate(x for x in brut or [] if isinstance(x, dict) and x.get("url")):
        organique.append({"rang": it.get("position") or i + 1, "url": it["url"], "domaine": domaine(it["url"]),
                          "titre": it.get("title") or "", "description": it.get("description") or ""})
    organique.sort(key=lambda o: o["rang"])
    return {"source": "Firecrawl", "organique": organique, "questions": [], "recherches_associees": [],
            "ai_overview": {"present": False, "mesure": False, "sources": [], "extrait": ""},
            "extrait_optimise": None, "features": []}


def lire_questions(texte: str) -> list[str]:
    """Une question par ligne ; lignes vides et commentaires (#) ignorés."""
    return [l.strip().lstrip("-* ").strip() for l in (texte or "").splitlines()
            if l.strip() and not l.lstrip().startswith("#")]


# ─── Agrégation ───────────────────────────────────────────────────

def arrondi(n: float, pas: int = 50) -> int:
    return int(round(n / pas) * pas)


def longueur_cible(mots: list[int]) -> dict | None:
    """Médiane et 3e quartile des pages bien lues : la fourchette à viser, pas un objectif de remplissage."""
    lues = [m for m in mots if m >= MOTS_MINI]
    if len(lues) < 2:
        return None
    med, q3 = C.mediane(lues), C.centile(lues, 75)
    return {"pages": len(lues), "min": min(lues), "max": max(lues), "mediane": round(med), "p75": round(q3),
            "fourchette": [arrondi(med), max(arrondi(med), arrondi(q3))]}


def radicaux_cle(cle: str) -> set[str]:
    return C.radicaux_utiles(cle)


def signature(titre: str, cle: str) -> set[str]:
    """Les radicaux qui portent le sujet d'un titre, mot-clé retiré (il est dans tous les titres)."""
    base = C.radicaux_utiles(titre)
    return (base - radicaux_cle(cle)) or base


def proches(a: set[str], b: set[str]) -> bool:
    """Deux titres parlent-ils du même sujet ? Recouvrement des radicaux, tolérant pour les titres courts."""
    commun = len(a & b)
    if not commun:
        return False
    jaccard, inclusion = commun / len(a | b), commun / min(len(a), len(b))
    return (jaccard >= 0.5 or (commun >= 2 and inclusion >= 0.8)
            or (min(len(a), len(b)) <= 2 and inclusion >= 0.5 and jaccard >= 1 / 3))


def titre_generique(titre: str) -> bool:
    return bool(TITRES_GENERIQUES.match(C.sans_accents(titre).strip(" :?!.")))


def titres_de_section(page: dict) -> list[str]:
    """Les H2 de la page ; ses H3 si elle n'a pas de H2. Titres génériques (FAQ, sommaire…) exclus."""
    h2 = [t for n, t in page.get("plan") or [] if n == 2]
    h = h2 or [t for n, t in page.get("plan") or [] if n == 3]
    return [t for t in h if not titre_generique(t)]


def sujets(pages: list[dict], cle: str) -> list[dict]:
    """Regroupe les H2 des concurrents par sujet ; un sujet traité par plusieurs pages est attendu par Google."""
    groupes: list[dict] = []
    for p in pages:
        for t in titres_de_section(p):
            sig = signature(t, cle)
            if not sig:
                continue
            g = next((g for g in groupes if proches(sig, g["signature"])), None)
            if g is None:
                g = {"signature": sig, "formulations": [], "pages": [], "rangs": []}
                groupes.append(g)
            if t not in g["formulations"]:
                g["formulations"].append(t)
            if p["url"] not in g["pages"]:
                g["pages"].append(p["url"])
                g["rangs"].append(p.get("rang") or 99)
    groupes.sort(key=lambda g: (-len(g["pages"]), min(g["rangs"])))
    return [{"sujet": g["formulations"][0], "pages": len(g["pages"]), "formulations": g["formulations"][:4],
             "urls": g["pages"], "signature": sorted(g["signature"])} for g in groupes]


def couvert(texte: str, titres: list[str], cle: str, seuil: float = 0.6) -> bool:
    """Un titre de la liste reprend-il l'essentiel du sujet (60 % de ses radicaux utiles) ?"""
    sig = signature(texte, cle)
    if not sig:
        return True
    return any(len(sig & C.radicaux_utiles(t)) / len(sig) >= seuil for t in titres)


def champ_commun(pages: list[dict], client: dict | None = None, maxi: int = 30, cle: str = "") -> dict:
    """Termes présents sur au moins la moitié des pages lues (2 au minimum), et ceux absents du client.

    Les termes faits uniquement des mots du mot-clé sont écartés : ils sont partout, ils n'apprennent rien.
    """
    lues = [p for p in pages if p.get("mots", 0) >= MOTS_MINI]
    if len(lues) < 2:
        return {"seuil_pages": None, "pages_lues": len(lues), "expressions": [], "mots": [], "absents_client": []}
    seuil = max(2, math.ceil(len(lues) / 2))
    docs, total, formes = {}, {}, {}
    for p in lues:
        compte, f = C.termes(p.get("texte") or "")
        for k, n in compte.items():
            docs[k] = docs.get(k, 0) + 1
            total[k] = total.get(k, 0) + n
            formes.setdefault(k, f[k])
    mots_cle = {n for n, _ in C.jetons(cle)}
    retenus = sorted((k for k in docs if docs[k] >= seuil and not set(k.split()) <= mots_cle),
                     key=lambda k: (-docs[k], -total[k]))
    lignes = [{"terme": formes[k], "cle": k, "pages": docs[k], "occurrences": total[k]} for k in retenus]
    absents = []
    if client and client.get("texte"):
        compte_client, _ = C.termes(client["texte"])
        absents = [l for l in lignes if l["cle"] not in compte_client][:maxi]
    return {"seuil_pages": seuil, "pages_lues": len(lues),
            "expressions": [l for l in lignes if " " in l["cle"]][:maxi],
            "mots": [l for l in lignes if " " not in l["cle"]][:maxi], "absents_client": absents}


def ton_du_top(pages: list[dict]) -> dict:
    tons = [C.mesures_ton(p) for p in pages if p.get("mots", 0) >= MOTS_MINI]
    if not tons:
        return {}
    compte = lambda cle: {v: sum(1 for t in tons if t[cle] == v) for v in {t[cle] for t in tons}}  # noqa: E731
    phrases = [t["phrase_moyenne"] for t in tons if t["phrase_moyenne"]]
    lis = [t["lisibilite"] for t in tons if t["lisibilite"] is not None]
    return {"pages": len(tons), "adresse": compte("adresse"), "personne": compte("personne"),
            "phrase_moyenne_mediane": round(C.mediane(phrases), 1) if phrases else None,
            "lisibilite_mediane": round(C.mediane(lis), 1) if lis else None}


def entites_communes(pages: list[dict], cle: str = "", maxi: int = 30) -> dict:
    """Entités nommées (noms propres, outils, sigles) par nombre de pages du top qui les citent.

    Celles qu'au moins deux pages citent forment le socle attendu ; les autres sont des pistes.
    Le mot-clé lui-même est écarté (« GEO » sur « audit geo » n'apprend rien).
    """
    lues = [p for p in pages if p.get("mots", 0) >= MOTS_MINI]
    docs, total, formes = {}, {}, {}
    mots_cle = C.sans_accents(cle)
    for p in lues:
        for e in p.get("entites") or C.entites_nommees(p.get("texte") or ""):
            k = e["cle"]
            if k == mots_cle or set(k.split()) <= set(mots_cle.split()):
                continue
            docs[k] = docs.get(k, 0) + 1
            total[k] = total.get(k, 0) + e["occurrences"]
            formes.setdefault(k, e["entite"])
    ordre = sorted(docs, key=lambda k: (-docs[k], -total[k]))
    lignes = [{"entite": formes[k], "pages": docs[k], "occurrences": total[k]} for k in ordre]
    return {"pages_lues": len(lues), "communes": [l for l in lignes if l["pages"] >= 2][:maxi],
            "isolees": [l for l in lignes if l["pages"] == 1][:maxi]}


def candidats_maillage(urls: list[str], mot: str, champ: dict | None = None, maxi: int = 12) -> list[dict]:
    """Pages du site du client dont l'adresse parle du sujet : candidates au maillage interne.

    Score = radicaux du mot-clé présents dans le chemin (×3) + termes du champ commun (×1). Un lien se
    décide à la lecture de la page cible ; la liste dit seulement où regarder d'abord.
    """
    cle = C.radicaux_utiles(mot)
    champ_r = set()
    for x in (champ or {}).get("expressions", []) + (champ or {}).get("mots", []):
        champ_r |= C.radicaux_utiles(x["terme"])
    champ_r -= cle
    sortie = []
    for u in dict.fromkeys(urls):
        chemin = urlparse(u).path.replace("-", " ").replace("_", " ").replace("/", " ")
        r = C.radicaux_utiles(chemin)
        score = 3 * len(r & cle) + len(r & champ_r)
        if score:
            sortie.append({"url": u, "score": score, "communs": sorted((r & cle) | (r & champ_r))})
    sortie.sort(key=lambda x: (-x["score"], len(x["url"])))
    return sortie[:maxi]


def construire(mot: str, lieu: str, langue: str, serp: dict, pages: list[dict], client: dict | None,
               date: str, echecs: list[dict] | None = None, sitemap: list[str] | None = None) -> dict:
    """Assemble le rapport à partir de la SERP et des pages déjà lues. Pur : aucun réseau."""
    lues = [p for p in pages if p.get("mots", 0) >= MOTS_MINI]
    tous_sujets = sujets(lues, mot)
    recurrents = [s for s in tous_sujets if s["pages"] >= 2]
    isoles = [s for s in tous_sujets if s["pages"] == 1]
    titres_top = [t for p in lues for _, t in p.get("plan") or []]
    questions = [{"question": q, "source": "PAA", "traitee_par_le_top": couvert(q, titres_top, mot)}
                 for q in serp["questions"]]
    for p in lues:
        for q in p.get("questions_titres") or []:
            if not any(C.radicaux_utiles(q) == C.radicaux_utiles(x["question"]) for x in questions):
                questions.append({"question": q, "source": domaine(p["url"]), "traitee_par_le_top": True})
    rapport = {
        "mot": mot, "lieu": lieu, "langue": langue, "date": date,
        "serp": serp,
        "pages": [{**{k: v for k, v in p.items() if k not in ("texte", "paragraphes", "markdown")},
                   "ton": C.mesures_ton(p), "ouverture": C.ouverture(p)} for p in pages],
        "echecs": echecs or [],
        "longueur": longueur_cible([p["mots"] for p in pages]),
        "structure": {
            "pages_lues": len(lues),
            "avec_faq": sum(1 for p in lues if p["faq"]),
            "avec_tableau": sum(1 for p in lues if p["tableaux"]),
            "avec_liste": sum(1 for p in lues if p["listes"]["puces"] + p["listes"]["numerotees"]),
            "h2_mediane": C.mediane([sum(1 for n, _ in p["plan"] if n == 2) for p in lues]) if lues else None,
            "images_mediane": C.mediane([p["images"] for p in lues]) if lues else None,
            "avec_video": sum(1 for p in lues if p.get("videos")),
            "schemas": sorted({s for p in lues for s in p["schemas"]}),
        },
        "sujets_recurrents": recurrents,
        "sujets_isoles": isoles[:15],
        "questions": questions,
        "champ": champ_commun(pages, client, cle=mot),
        "entites": entites_communes(pages, mot),
        "ton": ton_du_top(pages),
        "client": None,
        "maillage": None,
    }
    if sitemap is not None:
        rapport["maillage"] = {"urls_sitemap": len(sitemap),
                               "candidats": candidats_maillage(sitemap, mot, rapport["champ"])}
    if client:
        titres_client = [t for _, t in client.get("plan") or []]
        dom = domaine(client["url"])
        position = next((o["rang"] for o in serp["organique"] if o["domaine"] == dom), None)
        lg = rapport["longueur"]
        rapport["client"] = {
            "url": client["url"], "position": position, "mots": client.get("mots"),
            "ecart_mots": (client["mots"] - lg["mediane"]) if lg and client.get("mots") is not None else None,
            "plan": client.get("plan"),
            "sujets_manquants": [s for s in recurrents if not any(proches(set(s["signature"]), signature(t, mot))
                                                                 for t in titres_client)],
            "questions_non_traitees": [q["question"] for q in questions if q["source"] == "PAA"
                                       and not couvert(q["question"], titres_client, mot)],
            "cite_par_ai_overview": any(s["domaine"] == dom
                                        for s in serp["ai_overview"]["sources"]),
            "faq": client.get("faq"), "tableaux": client.get("tableaux"), "schemas": client.get("schemas"),
            "ton": C.mesures_ton(client),
        }
    return rapport


# ─── Rendu ────────────────────────────────────────────────────────

def _cellule(t) -> str:
    return str(t if t is not None else "n.d.").replace("|", "/").replace("\n", " ")


def _repartition(d: dict) -> str:
    return ", ".join(f"{k} {v}" for k, v in sorted(d.items(), key=lambda x: -x[1])) if d else "n.d."


def markdown(r: dict) -> str:
    s, lg, st = r["serp"], r["longueur"], r["structure"]
    aio = s["ai_overview"]
    L = [f"# SERP — « {r['mot']} »", "",
         f"{r['lieu']} · {r['langue']} · relevé le {r['date']} · SERP {s.get('source', 'DataForSEO')} · "
         f"{st['pages_lues']} page(s) concurrente(s) lue(s)", "",
         "## Synthèse", "", "| Signal | Mesure |", "|---|---|",
         f"| Longueur du top (mots) | " + (f"médiane {lg['mediane']} · 3e quartile {lg['p75']} · "
                                          f"de {lg['min']} à {lg['max']} ({lg['pages']} pages)" if lg else "n.d.") + " |",
         f"| **Fourchette cible** | " + (("**environ {0} mots**" if lg["fourchette"][0] == lg["fourchette"][1]
                                        else "**{0} à {1} mots**").format(*lg["fourchette"]) if lg else "n.d.") + " |",
         f"| AI Overview | " + ("non mesuré (SERP sans features)" if not aio.get("mesure", True)
                                 else ("oui" if aio["present"] else "non")
                                 + (f" · {len(aio['sources'])} source(s) citée(s)" if aio["present"] else "")) + " |",
         f"| Extrait optimisé (position 0) | "
         + (f"{s['extrait_optimise']['domaine']}" if s["extrait_optimise"]
            else "non" if aio.get("mesure", True) else "non mesuré") + " |",
         f"| FAQ / tableau / liste | {st['avec_faq']} / {st['avec_tableau']} / {st['avec_liste']} "
         f"sur {st['pages_lues']} pages |",
         f"| H2 par page (médiane) | {_cellule(st['h2_mediane'])} |",
         f"| Vidéo intégrée | {st.get('avec_video', 0)} sur {st['pages_lues']} pages |",
         f"| Schémas vus | {', '.join(st['schemas']) or 'aucun'} |",
         f"| Features de la SERP | {', '.join(s['features']) or 'n.d.'} |", ""]
    if r["ton"]:
        t = r["ton"]
        L += [f"**Ton du top** : adresse {_repartition(t['adresse'])} · personne {_repartition(t['personne'])} · "
              f"phrase moyenne {_cellule(t['phrase_moyenne_mediane'])} mots · lisibilité "
              f"{_cellule(t['lisibilite_mediane'])} (Kandel-Moles, indicatif).", ""]

    L += ["## Top organique", "",
          "| # | Domaine | Title | Mots | H2 | Listes | Tabl. | Img / vid. | FAQ | Schémas | Mise à jour |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    lues = {p["url"]: p for p in r["pages"]}
    dom_client = domaine(r["client"]["url"]) if r["client"] else None
    for o in s["organique"]:
        p = lues.get(o["url"])
        if o["domaine"] == dom_client:
            L.append(f"| {o['rang']} | **{o['domaine']}** (client) | {_cellule(o['titre'])} | "
                     f"{_cellule(r['client']['mots'])} | | | | | | | |")
            continue
        if p:
            nb_h2 = sum(1 for n, _ in p["plan"] if n == 2)
            L.append(f"| {o['rang']} | {o['domaine']} | {_cellule(o['titre'])} | {p['mots']} | {nb_h2} | "
                     f"{p['listes']['puces'] + p['listes']['numerotees']} | {p['tableaux']} | "
                     f"{p['images']} / {p.get('videos', 0)} | {'oui' if p['faq'] else 'non'} | {', '.join(p['schemas'][:4]) or '—'} | "
                     f"{p['dates'].get('modifiee') or p['dates'].get('publiee') or '—'} |")
        else:
            L.append(f"| {o['rang']} | {o['domaine']} | {_cellule(o['titre'])} | — | | | | | | | |")
    if r["echecs"]:
        L += ["", "Pages non lues : " + " · ".join(f"{e['url']} ({e['raison']})" for e in r["echecs"])]
    L.append("")

    L += ["## Sujets récurrents (H2 traités par au moins 2 pages)", ""]
    if r["sujets_recurrents"]:
        L += ["| Sujet | Pages | Formulations vues |", "|---|---|---|"]
        L += [f"| {_cellule(x['sujet'])} | {x['pages']} | {_cellule(' / '.join(x['formulations']))} |"
              for x in r["sujets_recurrents"]]
    else:
        L.append("Aucun sujet commun : SERP hétérogène, ou pages mal lues.")
    if r["sujets_isoles"]:
        L += ["", "**Traités par une seule page** (angle propre, ou piste d'information gain) :", ""]
        L += [f"- {x['sujet']} — {domaine(x['urls'][0])}" for x in r["sujets_isoles"]]
    L.append("")

    L += ["## Questions", ""]
    if r["questions"]:
        L += ["| Question | Source | Traitée dans un titre du top |", "|---|---|---|"]
        L += [f"| {_cellule(q['question'])} | {q['source']} | {'oui' if q['traitee_par_le_top'] else '**non**'} |"
              for q in r["questions"]]
    else:
        L.append("Aucune question PAA ni titre interrogatif.")
    L.append("")

    L += ["## AI Overview", ""]
    if not aio.get("mesure", True):
        L.append("Non mesuré : la SERP vient d'une source sans features (Firecrawl). À relever à la main "
                 "ou par DataForSEO avant d'écrire la section 3 du brief.")
    elif aio["present"]:
        L += [f"> {aio['extrait']}" if aio["extrait"] else "> (contenu non renvoyé)", "", "Sources citées :", ""]
        L += [f"- {x['domaine']} — {x['titre'] or x['url']}" for x in aio["sources"]] or ["- aucune renvoyée"]
    else:
        L.append("Absent sur cette requête au moment du relevé.")
    L.append("")

    if s["recherches_associees"]:
        L += ["## Recherches associées", "", " · ".join(s["recherches_associees"]), ""]

    ch = r["champ"]
    L += ["## Champ sémantique commun", ""]
    if ch["seuil_pages"]:
        L.append(f"Termes présents sur au moins {ch['seuil_pages']} des {ch['pages_lues']} pages lues.")
        L += ["", "**Expressions** : " + (", ".join(f"{x['terme']} ({x['pages']})" for x in ch["expressions"]) or "—"),
              "", "**Mots** : " + (", ".join(f"{x['terme']} ({x['pages']})" for x in ch["mots"]) or "—")]
    else:
        L.append("n.d. : moins de deux pages lues.")
    L.append("")

    en = r.get("entites") or {}
    L += ["## Entités nommées du top", ""]
    if en.get("communes") or en.get("isolees"):
        L += ["Heuristique (noms propres, outils, sigles) : à trier, une marque concurrente n'entre pas dans le "
              "noyau.", "",
              "**Citées par au moins 2 pages** : "
              + (", ".join(f"{x['entite']} ({x['pages']})" for x in en.get("communes", [])) or "—"), "",
              "**Citées par une seule page** : " + (", ".join(x["entite"] for x in en.get("isolees", [])[:20]) or "—")]
    else:
        L.append("n.d. : aucune page lue.")
    L.append("")

    m = r.get("maillage")
    if m is not None:
        L += ["## Maillage interne — candidates du sitemap", "",
              f"{m['urls_sitemap']} adresse(s) lue(s) dans le sitemap. Pages dont le chemin parle du sujet "
              "(à confirmer à la lecture) :", ""]
        L += [f"- {x['url']} — {', '.join(x['communs'])}" for x in m["candidats"]] or ["- aucune"]
        L.append("")

    c = r["client"]
    if c:
        L += ["## Page du client face au top", "", f"URL : {c['url']}", "",
              "| Signal | Client | Top |", "|---|---|---|",
              f"| Position | {_cellule(c['position']) if c['position'] else 'hors top 10'} | |",
              f"| Mots | {_cellule(c['mots'])} | médiane {lg['mediane'] if lg else 'n.d.'} |",
              f"| FAQ | {'oui' if c['faq'] else 'non'} | {st['avec_faq']}/{st['pages_lues']} |",
              f"| Tableaux | {_cellule(c['tableaux'])} | {st['avec_tableau']}/{st['pages_lues']} avec tableau |",
              f"| Citée par l'AI Overview | {'oui' if c['cite_par_ai_overview'] else 'non'} | |",
              f"| Adresse / personne | {c['ton']['adresse']} / {c['ton']['personne']} | "
              f"{_repartition(r['ton'].get('adresse', {})) if r['ton'] else 'n.d.'} |", ""]
        L += ["**Sujets récurrents absents de ses titres** :", ""]
        L += [f"- {x['sujet']} ({x['pages']} pages)" for x in c["sujets_manquants"]] or ["- aucun"]
        L += ["", "**Questions PAA sans titre qui y réponde** :", ""]
        L += [f"- {q}" for q in c["questions_non_traitees"]] or ["- aucune"]
        L += ["", "**Termes du top absents de la page** : "
              + (", ".join(f"{x['terme']} ({x['pages']})" for x in ch["absents_client"]) or "aucun"), ""]

    L += ["## Plans Hn des concurrents", ""]
    for p in r["pages"]:
        L += [f"### {domaine(p['url'])} — {p['mots']} mots", "", p["url"], ""]
        L += [f"{'  ' * max(0, n - 1)}- H{n} {t}" for n, t in p["plan"]] or ["- (aucun titre lu)"]
        ton = p["ton"]
        L += ["", f"Ouverture : {p['ouverture']} · adresse : {ton['adresse']} · personne : {ton['personne']} · "
                  f"phrase moyenne : {_cellule(ton['phrase_moyenne'])} mots", ""]
    L += ["---", "", "Mesures brutes : elles disent ce que le top fait, pas ce qu'il faut faire. "
          "L'angle, l'information gain et le plan se décident dans le brief (`seo-brief`)."]
    return "\n".join(L) + "\n"


def contenus(r: dict, pages: list[dict]) -> str:
    L = [f"# Contenus du top — « {r['mot']} » ({r['date']})", "",
         "Contenu principal de chaque concurrent, titres et listes conservés. À lire avant d'écrire le brief : "
         "c'est ici que se voient les angles, les preuves, le ton et ce qui manque.", ""]
    for p in pages:
        md = p.get("markdown") or ""
        coupe = len(md) > BUDGET_CONTENU
        L += ["---", "", f"## Source : {p['url']}", "", f"Title : {p.get('titre') or '—'}",
              f"Meta : {p.get('meta') or '—'}", "", md[:BUDGET_CONTENU] + ("\n\n[… tronqué]" if coupe else ""), ""]
    return "\n".join(L)


def slug(texte: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", C.sans_accents(texte)).strip("-")[:60] or "requete"


# ─── Réseau ───────────────────────────────────────────────────────

def lire_dataforseo(url: str, langue: str) -> tuple[dict, float]:
    """Repli payant : la page rendue par DataForSEO (JavaScript exécuté), en Markdown."""
    res, cout = demande.appel("on_page/content_parsing/live",
                              [{"url": url, "enable_javascript": True, "markdown_view": True,
                                "accept_language": langue, "disable_cookie_popup": True}])
    items = [it for r in res for it in (r.get("items") or [])]
    md = next((it.get("page_as_markdown") for it in items if it.get("page_as_markdown")), "")
    if not md:
        raise C.PageIllisible("DataForSEO n'a rien rendu")
    return C.lire_markdown(md, url), cout


def lire_pages_json(brut) -> dict[str, dict]:
    """Pages déjà relevées (Firecrawl scrape, export d'outil) : liste de {url, html | markdown}, ou un
    dictionnaire {url: {html | markdown}}. La réponse brute de firecrawl_scrape (clé « data ») est acceptée."""
    if isinstance(brut, dict) and not brut.get("url"):
        brut = [{"url": u, **(v if isinstance(v, dict) else {"markdown": v})} for u, v in brut.items()]
    sortie = {}
    for it in brut if isinstance(brut, list) else [brut]:
        if not isinstance(it, dict):
            continue
        d = it.get("data") if isinstance(it.get("data"), dict) else it
        url = it.get("url") or d.get("url") or (d.get("metadata") or {}).get("sourceURL")
        if url and (d.get("html") or d.get("rawHtml") or d.get("markdown")):
            sortie[url] = d
    return sortie


def lire_page_relevee(url: str, d: dict) -> dict:
    """Le HTML d'abord (schémas, dates, méta), le Markdown sinon."""
    html = d.get("rawHtml") or d.get("html")
    page = C.lire_html(html, url) if html else C.lire_markdown(d.get("markdown") or "", url)
    if html and d.get("markdown") and page["mots"] < MOTS_MINI:
        page = C.lire_markdown(d["markdown"], url)     # HTML rendu côté client : le Markdown du relevé est plus sûr
    meta = d.get("metadata") or {}
    page["titre"] = page["titre"] or meta.get("title") or ""
    page["meta"] = page["meta"] or meta.get("description") or ""
    return page


def lire_page(url: str, langue: str, repli: bool, relevees: dict | None = None) -> tuple[dict | None, str | None, float]:
    """(page, raison de l'échec, coût). Ne lève jamais : une page illisible est une ligne du rapport."""
    raison, cout = None, 0.0
    if relevees and url in relevees:
        page = lire_page_relevee(url, relevees[url])
        if page["mots"] >= MOTS_MINI:
            return page, None, 0.0
        return page, f"{page['mots']} mots dans le relevé fourni", 0.0
    try:
        html, finale = C.telecharger(url, langue=langue)
        page = C.lire_html(html, url)
        if page["mots"] >= MOTS_MINI:
            return page, None, 0.0
        raison = f"{page['mots']} mots lus (page rendue en JavaScript ou bloquée)"
    except C.PageIllisible as exc:
        page, raison = None, str(exc)
    if repli:
        try:
            p2, cout = lire_dataforseo(url, langue)
            if p2["mots"] >= (page or {}).get("mots", 0):
                return p2, None, cout
        except (C.PageIllisible, demande.ErreurAPI) as exc:
            raison = f"{raison} ; repli DataForSEO : {exc}"
    return page, raison, cout


def main() -> int:
    charger_env()
    ap = argparse.ArgumentParser(description="SERP d'un mot-clé et lecture des pages concurrentes")
    ap.add_argument("--mot", required=True, help="mot-clé")
    ap.add_argument("--langue", help="fr, en, ar…")
    ap.add_argument("--pays", help="code ISO, défaut : projet.pays_cible")
    ap.add_argument("--lieu", help="nom de lieu DataForSEO, pour un pays hors liste")
    ap.add_argument("--top", type=int, default=5, help="pages concurrentes à lire (défaut 5, max 10)")
    ap.add_argument("--url", help="page du client à comparer (sinon : celle de projet.domaine si elle ranke)")
    ap.add_argument("--repli-dataforseo", action="store_true",
                    help="relire par DataForSEO les pages illisibles (payant)")
    ap.add_argument("--serp-json", help="réponse SERP DataForSEO déjà enregistrée (évite de repayer l'appel)")
    ap.add_argument("--serp-firecrawl", help="résultat d'une recherche Firecrawl enregistré (repli sans DataForSEO)")
    ap.add_argument("--questions", help="fichier de questions (une par ligne) : PAA relevées ailleurs")
    ap.add_argument("--pages-json", help="pages déjà relevées : [{url, html | markdown}] (ex. Firecrawl scrape)")
    ap.add_argument("--sitemap", help="sitemap du client (URL ou fichier) : candidates au maillage interne")
    ap.add_argument("--sortie", help="dossier de sortie, défaut : recherche/ du projet")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    lieu, langue = demande.lieu_et_langue(a)
    cout = 0.0
    try:
        if a.serp_firecrawl:
            resultats = None
        elif a.serp_json:
            brut = json.loads(Path(a.serp_json).read_text(encoding="utf-8"))
            resultats = [r for t in brut.get("tasks", []) for r in t.get("result") or []] \
                if isinstance(brut, dict) else brut
        else:
            resultats, cout = demande.appel("serp/google/organic/live/advanced", [{
                "keyword": a.mot, "location_name": lieu, "language_code": langue, "device": "desktop",
                "depth": 10, "people_also_ask_click_depth": 1, "load_async_ai_overview": True}])
            print(f"  SERP : {cout:.4f} $", file=sys.stderr)
    except demande.ErreurAPI as exc:
        print(f"✗ DataForSEO : {exc}", file=sys.stderr)
        return 1
    serp = lire_serp_firecrawl(json.loads(Path(a.serp_firecrawl).read_text(encoding="utf-8"))) \
        if a.serp_firecrawl else lire_serp(resultats)
    if a.questions:
        serp["questions"] = list(dict.fromkeys(serp["questions"]
                                               + lire_questions(Path(a.questions).read_text(encoding="utf-8"))))
    relevees = lire_pages_json(json.loads(Path(a.pages_json).read_text(encoding="utf-8"))) if a.pages_json else {}

    dom_client = domaine(a.url) if a.url else domaine(lire_valeur("projet.domaine"))
    url_client = a.url or next((o["url"] for o in serp["organique"] if dom_client and o["domaine"] == dom_client),
                               None)
    cibles = [o for o in serp["organique"] if not (dom_client and o["domaine"] == dom_client)][:max(1, min(a.top, 10))]

    pages, echecs = [], []
    for o in cibles:
        page, raison, c = lire_page(o["url"], langue, a.repli_dataforseo, relevees)
        cout += c
        if c:
            print(f"  repli {o['domaine']} : {c:.4f} $", file=sys.stderr)
        if page:
            page["rang"] = o["rang"]
            pages.append(page)
        if raison:
            echecs.append({"url": o["url"], "raison": raison})
        print(f"  {'✓' if not raison else '·'} {o['rang']:>2}. {o['domaine']} — "
              f"{page['mots'] if page else 0} mots{'' if not raison else ' (' + raison + ')'}", file=sys.stderr)

    client = None
    if url_client:
        client, raison, c = lire_page(url_client, langue, a.repli_dataforseo, relevees)
        cout += c
        if raison:
            print(f"  · page du client : {raison}", file=sys.stderr)

    date = dt.date.today().isoformat()
    sitemap = None
    if a.sitemap:
        import cartographie  # noqa: E402 — seulement si l'option est demandée
        try:
            if Path(a.sitemap).exists():
                locs, _ = cartographie.urls_du_sitemap(Path(a.sitemap).read_text(encoding="utf-8"))
                sitemap = [u for u in locs if not cartographie.PAS_UNE_PAGE.search(u)]
            else:
                sitemap = cartographie.lire_sitemap(a.sitemap)
        except Exception as exc:  # noqa: BLE001 — un sitemap illisible n'empêche pas le rapport
            print(f"  · sitemap illisible : {str(exc)[:80]}", file=sys.stderr)
    rapport = construire(a.mot, lieu, langue, serp, pages, client, date, echecs, sitemap)
    dossier = Path(a.sortie) if a.sortie else racine_projet() / "recherche"
    dossier.mkdir(parents=True, exist_ok=True)
    base = f"serp-{slug(a.mot)}-{date}"
    (dossier / f"{base}.md").write_text(markdown(rapport), encoding="utf-8")
    (dossier / f"{base}-contenus.md").write_text(contenus(rapport, pages), encoding="utf-8")
    rapport["cout_usd"] = round(cout, 4)

    if a.json:
        print(json.dumps(rapport, ensure_ascii=False, indent=1))
    else:
        lg = rapport["longueur"]
        aio = serp["ai_overview"]
        print(f"\n  « {a.mot} » · {lieu} · {langue} · SERP {serp['source']} · AI Overview : "
              f"{'non mesuré' if not aio['mesure'] else 'oui' if aio['present'] else 'non'} · "
              f"{len(pages)} page(s) lue(s)")
        print(f"  fourchette cible : {lg['fourchette'][0]}-{lg['fourchette'][1]} mots" if lg
              else "  fourchette cible : n.d.")
        print(f"  sujets récurrents : {len(rapport['sujets_recurrents'])} · questions : {len(rapport['questions'])}")
    print(f"  ✓ {dossier / (base + '.md')}", file=sys.stderr)
    print(f"\n  coût DataForSEO : {cout:.4f} $\n", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
