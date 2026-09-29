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
    return {"organique": organique, "questions": list(dict.fromkeys(questions)),
            "recherches_associees": [a for a in dict.fromkeys(associees) if a],
            "ai_overview": aio, "extrait_optimise": extrait_position0, "features": sorted(features)}


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


def construire(mot: str, lieu: str, langue: str, serp: dict, pages: list[dict], client: dict | None,
               date: str, echecs: list[dict] | None = None) -> dict:
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
            "schemas": sorted({s for p in lues for s in p["schemas"]}),
        },
        "sujets_recurrents": recurrents,
        "sujets_isoles": isoles[:15],
        "questions": questions,
        "champ": champ_commun(pages, client, cle=mot),
        "ton": ton_du_top(pages),
        "client": None,
    }
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
         f"{r['lieu']} · {r['langue']} · relevé le {r['date']} · {st['pages_lues']} page(s) concurrente(s) lue(s)", "",
         "## Synthèse", "", "| Signal | Mesure |", "|---|---|",
         f"| Longueur du top (mots) | " + (f"médiane {lg['mediane']} · 3e quartile {lg['p75']} · "
                                          f"de {lg['min']} à {lg['max']} ({lg['pages']} pages)" if lg else "n.d.") + " |",
         f"| **Fourchette cible** | " + (("**environ {0} mots**" if lg["fourchette"][0] == lg["fourchette"][1]
                                        else "**{0} à {1} mots**").format(*lg["fourchette"]) if lg else "n.d.") + " |",
         f"| AI Overview | {'oui' if aio['present'] else 'non'}"
         + (f" · {len(aio['sources'])} source(s) citée(s)" if aio["present"] else "") + " |",
         f"| Extrait optimisé (position 0) | "
         + (f"{s['extrait_optimise']['domaine']}" if s["extrait_optimise"] else "non") + " |",
         f"| FAQ / tableau / liste | {st['avec_faq']} / {st['avec_tableau']} / {st['avec_liste']} "
         f"sur {st['pages_lues']} pages |",
         f"| H2 par page (médiane) | {_cellule(st['h2_mediane'])} |",
         f"| Schémas vus | {', '.join(st['schemas']) or 'aucun'} |",
         f"| Features de la SERP | {', '.join(s['features']) or 'n.d.'} |", ""]
    if r["ton"]:
        t = r["ton"]
        L += [f"**Ton du top** : adresse {_repartition(t['adresse'])} · personne {_repartition(t['personne'])} · "
              f"phrase moyenne {_cellule(t['phrase_moyenne_mediane'])} mots · lisibilité "
              f"{_cellule(t['lisibilite_mediane'])} (Kandel-Moles, indicatif).", ""]

    L += ["## Top organique", "", "| # | Domaine | Title | Mots | H2 | Listes | Tabl. | FAQ | Schémas | Mise à jour |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    lues = {p["url"]: p for p in r["pages"]}
    dom_client = domaine(r["client"]["url"]) if r["client"] else None
    for o in s["organique"]:
        p = lues.get(o["url"])
        if o["domaine"] == dom_client:
            L.append(f"| {o['rang']} | **{o['domaine']}** (client) | {_cellule(o['titre'])} | "
                     f"{_cellule(r['client']['mots'])} | | | | | | |")
            continue
        if p:
            nb_h2 = sum(1 for n, _ in p["plan"] if n == 2)
            L.append(f"| {o['rang']} | {o['domaine']} | {_cellule(o['titre'])} | {p['mots']} | {nb_h2} | "
                     f"{p['listes']['puces'] + p['listes']['numerotees']} | {p['tableaux']} | "
                     f"{'oui' if p['faq'] else 'non'} | {', '.join(p['schemas'][:4]) or '—'} | "
                     f"{p['dates'].get('modifiee') or p['dates'].get('publiee') or '—'} |")
        else:
            L.append(f"| {o['rang']} | {o['domaine']} | {_cellule(o['titre'])} | — | | | | | | |")
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
    if aio["present"]:
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


def lire_page(url: str, langue: str, repli: bool) -> tuple[dict | None, str | None, float]:
    """(page, raison de l'échec, coût). Ne lève jamais : une page illisible est une ligne du rapport."""
    raison, cout = None, 0.0
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
    ap.add_argument("--serp-json", help="réponse SERP déjà enregistrée (évite de repayer l'appel)")
    ap.add_argument("--sortie", help="dossier de sortie, défaut : recherche/ du projet")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    lieu, langue = demande.lieu_et_langue(a)
    cout = 0.0
    try:
        if a.serp_json:
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
    serp = lire_serp(resultats)

    dom_client = domaine(a.url) if a.url else domaine(lire_valeur("projet.domaine"))
    url_client = a.url or next((o["url"] for o in serp["organique"] if dom_client and o["domaine"] == dom_client),
                               None)
    cibles = [o for o in serp["organique"] if not (dom_client and o["domaine"] == dom_client)][:max(1, min(a.top, 10))]

    pages, echecs = [], []
    for o in cibles:
        page, raison, c = lire_page(o["url"], langue, a.repli_dataforseo)
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
        client, raison, c = lire_page(url_client, langue, a.repli_dataforseo)
        cout += c
        if raison:
            print(f"  · page du client : {raison}", file=sys.stderr)

    date = dt.date.today().isoformat()
    rapport = construire(a.mot, lieu, langue, serp, pages, client, date, echecs)
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
        print(f"\n  « {a.mot} » · {lieu} · {langue} · AI Overview : "
              f"{'oui' if serp['ai_overview']['present'] else 'non'} · {len(pages)} page(s) lue(s)")
        print(f"  fourchette cible : {lg['fourchette'][0]}-{lg['fourchette'][1]} mots" if lg
              else "  fourchette cible : n.d.")
        print(f"  sujets récurrents : {len(rapport['sujets_recurrents'])} · questions : {len(rapport['questions'])}")
    print(f"  ✓ {dossier / (base + '.md')}", file=sys.stderr)
    print(f"\n  coût DataForSEO : {cout:.4f} $\n", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
