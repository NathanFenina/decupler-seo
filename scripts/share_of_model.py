#!/usr/bin/env python3
"""Share of Model — la visibilité d'une marque dans les moteurs IA.

    python3 share_of_model.py --generer --categorie "cabinet d'expertise comptable" --sujets "création d'entreprise, tva" --pays France
    python3 share_of_model.py --verifier --prompts prompts.csv
    python3 share_of_model.py --prompts prompts.csv --concurrents "Cabinet A, Cabinet B"
    python3 share_of_model.py --prompts prompts.csv --sans-web      # notoriété : ce que les modèles savent de mémoire
    python3 share_of_model.py --moteurs openai,gemini --marque "Atlas Conseil" --domaine atlas-conseil.example

Moteurs, chacun interrogé avec sa recherche web (sauf --sans-web) :

    openai      OPENAI_API_KEY      ChatGPT (Responses API + web_search)
    gemini      GEMINI_API_KEY      Gemini + Google Search, le plus proche des AI Overviews
    claude      ANTHROPIC_API_KEY   Claude + web_search
    perplexity  PERPLEXITY_API_KEY  Sonar

Un moteur sans clé est ignoré ; sans aucune clé, le script prépare la grille de
relevé manuel. Modèles réglables : SOM_MODELE_OPENAI, SOM_MODELE_GEMINI,
SOM_MODELE_CLAUDE, SOM_MODELE_PERPLEXITY.

La liste de prompts (prompts.csv : famille,funnel,poids,sujet,prompt) :
- funnel TOFU (poids 1), MOFU (poids 2), BOFU (poids 3), répartis 2/3/3 par lot
  de 8 : un BOFU où la marque manque coûte plus qu'un TOFU ;
- jamais le nom de la marque dans les prompts de visibilité — sinon on mesure
  la notoriété de la question, pas celle de la marque ; les prompts qui la
  nomment vont dans la famille « marque » (réputation), comptée à part.

Mesures :
- taux de mention pondéré par le poids du funnel ;
- part de voix (SoV) face aux concurrents nommés (--concurrents) ;
- visibilité = 0,6 × taux de mention + 0,4 × SoV ;
- notoriété (--sans-web, mémoire du modèle) contre retrouvabilité (avec web) ;
- prompts manquants : poids > 1 et marque absente de tous les moteurs.

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
from collections import Counter
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import charger_env, lire_valeur  # noqa: E402

# Une 1re citation vaut plus qu'une 4e : le poids reflète ce qu'un lecteur
# retient réellement d'une réponse générée.
POIDS_RANG = {1: 1.0, 2: 0.6, 3: 0.4}
POIDS_DEFAUT = 0.2
POIDS_FUNNEL = {"TOFU": 1, "MOFU": 2, "BOFU": 3}

# Gabarits de départ : l'agent les reformule au ton parlé, puis --verifier
# contrôle les règles. {c} = catégorie, {s} = sujet, {p} = pays.
GABARITS = {
    # Chaque gabarit porte le sujet : sans lui, deux sujets produisent le même prompt.
    "fr": {"TOFU": ["Comment fonctionne {s} ?", "Que faut-il savoir sur {s} avant de se lancer ?"],
           "MOFU": ["Comment choisir un {c} pour {s} ?", "Quels critères comparer pour {s} ?",
                    "Quelles questions poser avant de confier {s} à un {c} ?"],
           "BOFU": ["Quel est le meilleur {c} pour {s} ?", "Quel {c} recommandes-tu pour {s} en {p} ?",
                    "À qui confier {s} en {p} ?"]},
    "en": {"TOFU": ["How does {s} work?", "What should I know about {s} before starting?"],
           "MOFU": ["How do I choose a {c} for {s}?", "What criteria matter most for {s}?",
                    "What should I ask before hiring a {c} for {s}?"],
           "BOFU": ["What is the best {c} for {s}?", "Which {c} do you recommend for {s} in {p}?",
                    "Who should handle {s} in {p}?"]},
}

# Formulations côté vendeur : un client ne pose pas la question ainsi.
COTE_VENDEUR = re.compile(r"g[ée]n[ée]ration de leads|lead gen|marque blanche|white label|nos clients|notre offre"
                          r"|our clients|our offer", re.I)

# Plateformes et outils qui ne sont ni des concurrents ni des sources à conquérir.
HORS_JEU = re.compile(r"(^|\.)(google|bing|openai|chatgpt|perplexity|anthropic|claude|gemini|schema|w3)\.", re.I)


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
# web=False : sans outil de recherche, pour mesurer ce que le modèle sait de mémoire.

def openai(prompt: str, web: bool = True) -> dict:
    corps = {"model": os.environ.get("SOM_MODELE_OPENAI", "gpt-5-mini"), "input": prompt}
    if web:
        corps["tools"] = [{"type": "web_search"}]
    d = _post("https://api.openai.com/v1/responses", corps, {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"})
    texte, sources = [], []
    for element in d.get("output", []):
        for contenu in element.get("content", []) or []:
            if contenu.get("type") == "output_text":
                texte.append(contenu.get("text", ""))
                sources += [domaine_de(a["url"]) for a in contenu.get("annotations", [])
                            if a.get("type") == "url_citation" and a.get("url")]
    return {"texte": "\n".join(texte), "sources": sources}


def gemini(prompt: str, web: bool = True) -> dict:
    modele = os.environ.get("SOM_MODELE_GEMINI", "gemini-2.5-flash")
    corps = {"contents": [{"parts": [{"text": prompt}]}]}
    if web:
        corps["tools"] = [{"google_search": {}}]
    d = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{modele}:generateContent", corps,
              {"x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    candidat = (d.get("candidates") or [{}])[0]
    texte = "".join(p.get("text", "") for p in candidat.get("content", {}).get("parts", []))
    sources = []
    for morceau in candidat.get("groundingMetadata", {}).get("groundingChunks", []):
        w = morceau.get("web", {})
        # L'URI est une redirection Google ; le titre porte le domaine de la source.
        titre = (w.get("title") or "").lower().removeprefix("www.")
        sources.append(titre if "." in titre and " " not in titre else domaine_de(w.get("uri", "")))
    return {"texte": texte, "sources": sources}


def claude(prompt: str, web: bool = True) -> dict:
    corps = {"model": os.environ.get("SOM_MODELE_CLAUDE", "claude-sonnet-5-5"), "max_tokens": 2048,
             "messages": [{"role": "user", "content": prompt}]}
    if web:
        corps["tools"] = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}]
    d = _post("https://api.anthropic.com/v1/messages", corps,
              {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"})
    texte, sources = [], []
    for bloc in d.get("content", []):
        if bloc.get("type") == "text":
            texte.append(bloc.get("text", ""))
            sources += [domaine_de(c["url"]) for c in bloc.get("citations", []) or [] if c.get("url")]
    return {"texte": "".join(texte), "sources": sources}


def perplexity(prompt: str, web: bool = True) -> dict:
    # Perplexity cherche toujours sur le web : il n'a pas de mode « mémoire ».
    d = _post("https://api.perplexity.ai/chat/completions",
              {"model": os.environ.get("SOM_MODELE_PERPLEXITY", "sonar"),
               "messages": [{"role": "user", "content": prompt}]},
              {"Authorization": f"Bearer {os.environ['PERPLEXITY_API_KEY']}"})
    citations = d.get("citations") or [r.get("url", "") for r in d.get("search_results", [])]
    return {"texte": d["choices"][0]["message"]["content"],
            "sources": [domaine_de(c if isinstance(c, str) else c.get("url", "")) for c in citations]}


MOTEURS = {"openai": ("OPENAI_API_KEY", openai), "gemini": ("GEMINI_API_KEY", gemini),
           "claude": ("ANTHROPIC_API_KEY", claude), "perplexity": ("PERPLEXITY_API_KEY", perplexity)}


def moteurs_disponibles(demandes: list[str] | None = None, sans_web: bool = False) -> list[str]:
    noms = demandes or list(MOTEURS)
    if sans_web:
        noms = [n for n in noms if n != "perplexity"]
    return [n for n in noms if n in MOTEURS and os.environ.get(MOTEURS[n][0], "").strip()]


# ─── Marque : alias et garde anti-homonyme ────────────────────────

def alias_marque(marque: str, domaine: str) -> list[str]:
    """Le nom, et la racine du domaine écrite des deux façons (« atlas-conseil », « atlas conseil »)."""
    racine = domaine.lower().removeprefix("www.").split(".")[0] if domaine else ""
    alias = {a.strip().lower() for a in (marque, racine, racine.replace("-", " ")) if a and len(a.strip()) >= 3}
    return sorted(alias, key=len, reverse=True)


def homonyme(texte: str, alias: list[str]) -> bool:
    """Le nom employé comme mot commun ou pour une autre activité : ce n'est pas une mention."""
    for a in alias:
        n = re.escape(a)
        if re.search(rf"\b(le|un|the) (mot|terme|word|term) «?\s*{n}\b|\b{n}\b»? (est|is) (un|une|a|an) "
                     rf"(mot|terme|verbe|nom commun|word|term|verb)\b|\b{n}\b»? (signifie|means|se réfère à|refers to)",
                     texte, re.I):
            return True
    return False


def mentionne(texte: str, alias: list[str]) -> bool:
    return any(re.search(rf"(?<![\w-]){re.escape(a)}(?![\w-])", texte, re.I) for a in alias) and not homonyme(texte, alias)


def rang_dans_liste(texte: str, alias: list[str]) -> int:
    """Rang de la marque dans l'énumération de la réponse (1 = citée en premier), 0 si absente."""
    items = [l for l in texte.splitlines() if re.match(r"\s*(\d+[.)]|[-*•]|\*\*)", l)]
    for i, l in enumerate(items, 1):
        if any(re.search(rf"(?<![\w-]){re.escape(a)}(?![\w-])", l, re.I) for a in alias):
            return i
    return 0


# ─── Analyse ──────────────────────────────────────────────────────

def sans_doublons(sources: list[str]) -> list[str]:
    vus, ordre = set(), []
    for s in sources:
        if s and s not in vus and not HORS_JEU.search(s):
            vus.add(s)
            ordre.append(s)
    return ordre


def analyser(reponse: dict, marque: str, domaine: str, concurrents: list[str] | None = None) -> dict:
    sources = sans_doublons(reponse["sources"])
    domaine = domaine.lower().removeprefix("www.")
    rang = next((i for i, s in enumerate(sources, 1) if domaine and (s == domaine or s.endswith("." + domaine))), 0)
    texte = reponse["texte"]
    alias = alias_marque(marque, domaine)
    nomme = bool(alias) and mentionne(texte, alias)
    cites = [c for c in (concurrents or []) if mentionne(texte, alias_marque(c, ""))]
    return {
        "cite": rang > 0, "rang": rang, "nomme": nomme,
        "rang_liste": rang_dans_liste(texte, alias) if nomme else 0,
        "concurrents_nommes": ", ".join(cites),
        "sources": ", ".join(sources[:8]),
        "extrait": next((p.strip() for p in re.split(r"(?<=[.!?])\s", texte)
                         if any(a in p.lower() for a in alias)), "")[:250],
    }


def synthese(releves: list[dict]) -> dict:
    """Par moteur : visibilité pondérée par le funnel sur les prompts non marqués."""
    par_moteur: dict[str, dict] = {}
    for r in releves:
        m = par_moteur.setdefault(r["moteur"], {"prompts": 0, "cites": 0, "nommes": 0, "poids": 0.0,
                                                 "poids_presents": 0.0, "poids_marque": 0.0, "poids_total": 0.0,
                                                 "mentions_marque": 0, "mentions_concurrents": 0, "reputation": 0})
        if r["famille"] == "marque":
            m["reputation"] += 1
            continue
        poids = float(r.get("poids") or 1)
        m["prompts"] += 1
        m["cites"] += bool(r["cite"])
        m["nommes"] += bool(r["nomme"])
        m["poids"] += poids
        m["poids_presents"] += poids if (r["cite"] or r["nomme"]) else 0
        m["mentions_marque"] += bool(r["nomme"])
        m["mentions_concurrents"] += len([c for c in str(r.get("concurrents_nommes", "")).split(", ") if c])
        nb = max(1, len([s for s in r["sources"].split(", ") if s]))
        m["poids_total"] += sum(POIDS_RANG.get(i, POIDS_DEFAUT) for i in range(1, nb + 1))
        if r["cite"]:
            m["poids_marque"] += POIDS_RANG.get(r["rang"], POIDS_DEFAUT)
    for m in par_moteur.values():
        n = m["prompts"] or 1
        m["taux_citation_pct"] = round(m["cites"] / n * 100, 1)
        m["taux_mention_pct"] = round(m["nommes"] / n * 100, 1)
        m["taux_mention_pondere_pct"] = round(m["poids_presents"] / m["poids"] * 100, 1) if m["poids"] else 0.0
        m["share_of_model_pct"] = round(m["poids_marque"] / m["poids_total"] * 100, 1) if m["poids_total"] else 0.0
        base = m["mentions_marque"] + m["mentions_concurrents"]
        m["sov_pct"] = round(m["mentions_marque"] / base * 100, 1) if base else None
        m["visibilite"] = round(0.6 * m["taux_mention_pondere_pct"] + 0.4 * (m["sov_pct"] or 0), 1) \
            if m["sov_pct"] is not None else m["taux_mention_pondere_pct"]
    return par_moteur


def prompts_manquants(releves: list[dict]) -> list[str]:
    """Poids > 1 et marque absente partout : les vraies priorités. Un TOFU absent n'est jamais un gap."""
    par_prompt: dict[str, list[dict]] = {}
    for r in releves:
        if r["famille"] != "marque" and float(r.get("poids") or 1) > 1:
            par_prompt.setdefault(r["prompt"], []).append(r)
    return [p for p, rs in par_prompt.items() if not any(r["cite"] or r["nomme"] for r in rs)]


def domaines_concurrents(releves: list[dict], domaine: str, n: int = 10) -> list[tuple[str, int]]:
    compte: Counter = Counter()
    for r in releves:
        if r["famille"] == "marque":
            continue
        for s in set(filter(None, r["sources"].split(", "))):
            if not (domaine and s.endswith(domaine)):
                compte[s] += 1
    return compte.most_common(n)


# ─── Liste de prompts : génération et vérification ────────────────

def generer(categorie: str, sujets: list[str], pays: str, langue: str = "fr", marque: str = "") -> list[dict]:
    g = GABARITS.get(langue, GABARITS["fr"])
    lignes = []
    for i, sujet in enumerate(sujets):
        # 2/3/3 par lot de 8 : on tourne dans les gabarits pour éviter les formulations répétées.
        for funnel, nb in (("TOFU", 2), ("MOFU", 3), ("BOFU", 3)):
            for k in range(nb):
                modele = g[funnel][(i + k) % len(g[funnel])]
                lignes.append({"famille": "visibilite", "funnel": funnel, "poids": POIDS_FUNNEL[funnel], "sujet": sujet,
                               "prompt": modele.format(c=categorie, s=sujet, p=pays)})
    if marque:
        for modele in ("Que vaut {m} ?", "Quels sont les avis sur {m} ?") if langue == "fr" else \
                      ("Is {m} any good?", "What do people say about {m}?"):
            lignes.append({"famille": "marque", "funnel": "", "poids": 0, "sujet": "", "prompt": modele.format(m=marque)})
    return lignes


def verifier(lignes: list[dict], marque: str, domaine: str) -> tuple[list[str], list[str]]:
    """Règles de la liste de prompts. Renvoie (erreurs, avertissements)."""
    erreurs, avert = [], []
    alias = alias_marque(marque, domaine)
    vus: set[str] = set()
    debuts: Counter = Counter()
    fins: Counter = Counter()
    funnels: Counter = Counter()
    for i, l in enumerate(lignes, 2):
        p = (l.get("prompt") or "").strip()
        fam = (l.get("famille") or "").strip()
        mots = p.split()
        if fam != "marque" and alias and any(re.search(rf"(?<![\w-]){re.escape(a)}(?![\w-])", p, re.I) for a in alias):
            erreurs.append(f"ligne {i} : la marque apparaît dans un prompt de visibilité — famille « marque » ou reformuler")
        if len(mots) > 20 or len(p) > 160:
            erreurs.append(f"ligne {i} : trop long ({len(mots)} mots, {len(p)} car. ; max 20 et 160)")
        if not p.endswith("?"):
            avert.append(f"ligne {i} : pas de point d'interrogation final")
        if p.lower() in vus:
            erreurs.append(f"ligne {i} : doublon")
        vus.add(p.lower())
        if COTE_VENDEUR.search(p):
            erreurs.append(f"ligne {i} : formulation côté vendeur (« {COTE_VENDEUR.search(p).group(0)} »)")
        if fam != "marque":
            funnels[(l.get("funnel") or "").upper()] += 1
            if len(mots) >= 3:
                debuts[" ".join(mots[:3]).lower()] += 1
                fins[" ".join(mots[-3:]).lower()] += 1
    for trio, n in list(debuts.items()) + list(fins.items()):
        if n > 3:
            avert.append(f"« {trio} » revient {n} fois : diversifier les formulations (3 au plus)")
    total = sum(funnels.values())
    if total and not funnels.get("BOFU"):
        avert.append("aucun prompt BOFU : ce sont eux qui mesurent si l'IA vous recommande")
    if total and funnels.get("", 0):
        avert.append(f"{funnels['']} prompt(s) sans funnel : poids 1 par défaut")
    return erreurs, avert


def lire_prompts(chemin: Path) -> list[dict]:
    with chemin.open(newline="", encoding="utf-8") as f:
        lignes = [l for l in csv.DictReader(f) if l.get("prompt")]
    for l in lignes:
        # Anciennes listes (famille,prompt) : poids par funnel s'il existe, sinon 1.
        funnel = (l.get("funnel") or "").upper()
        l["poids"] = float(l.get("poids") or POIDS_FUNNEL.get(funnel, 1))
        l["famille"] = (l.get("famille") or "visibilite").strip()
    return lignes


def grille_manuelle(prompts: list[dict], sortie: str) -> int:
    print("\n  Aucune clé de moteur IA — grille de relevé manuel préparée.")
    print("  Posez chaque prompt en session neuve, sans historique, dans la bonne")
    print("  langue et le bon pays, puis remplissez les colonnes.\n")
    with open(sortie, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["famille", "funnel", "poids", "prompt", "moteur", "cite", "rang", "nomme", "sources", "extrait"])
        for l in prompts:
            for moteur in ("ChatGPT", "Gemini", "AI Overview", "Claude", "Perplexity"):
                w.writerow([l["famille"], l.get("funnel", ""), l["poids"], l["prompt"], moteur, "", "", "", "", ""])
    print(f"  Grille écrite dans {sortie}\n")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Share of Model — visibilité dans les moteurs IA")
    p.add_argument("--prompts", default="prompts.csv")
    p.add_argument("--marque", default="", help="défaut : projet.nom de la config")
    p.add_argument("--domaine", default="", help="défaut : projet.domaine de la config")
    p.add_argument("--concurrents", default="", help="noms séparés par des virgules, pour la part de voix")
    p.add_argument("--moteurs", default="", help="ex. openai,gemini (défaut : tous ceux qui ont une clé)")
    p.add_argument("--sans-web", action="store_true", help="notoriété : modèles interrogés sans recherche web")
    p.add_argument("--generer", action="store_true", help="écrit une liste de départ dans --prompts")
    p.add_argument("--categorie", default="", help="avec --generer : la catégorie en toutes lettres, jamais un sigle")
    p.add_argument("--sujets", default="", help="avec --generer : 3 à 8 sujets séparés par des virgules")
    p.add_argument("--pays", default="France")
    p.add_argument("--langue", default="fr", choices=sorted(GABARITS))
    p.add_argument("--verifier", action="store_true", help="contrôle la liste sans interroger les moteurs")
    p.add_argument("--exporter", default="")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    charger_env()
    marque = args.marque or lire_valeur("projet.nom")
    domaine = domaine_de(args.domaine if "//" in args.domaine else f"https://{args.domaine}") if args.domaine \
        else domaine_de(lire_valeur("projet.domaine"))
    chemin = Path(args.prompts)

    if args.generer:
        sujets = [s.strip() for s in args.sujets.split(",") if s.strip()]
        if not args.categorie or not sujets:
            raise SystemExit("✗ --generer demande --categorie et --sujets")
        lignes = generer(args.categorie, sujets, args.pays, args.langue, marque)
        with chemin.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["famille", "funnel", "poids", "sujet", "prompt"])
            w.writeheader()
            w.writerows(lignes)
        print(f"\n  {len(lignes)} prompts écrits dans {chemin}. Reformulez-les au ton parlé d'un client,")
        print("  puis --verifier. Une fois la liste validée, ne la changez plus : on ajoute, on ne retire pas.\n")
        return 0

    if not chemin.exists():
        print(f"\n  Fichier de prompts introuvable : {args.prompts}")
        print("  Créez-en un avec --generer --categorie … --sujets …\n")
        return 1
    prompts = lire_prompts(chemin)

    erreurs, avert = verifier(prompts, marque, domaine)
    if args.verifier or erreurs:
        for e in erreurs:
            print(f"  ✗ {e}")
        for a in avert:
            print(f"  ! {a}")
        if args.verifier:
            print("\n  " + ("✗ Liste à corriger." if erreurs else f"✓ {len(prompts)} prompts conformes.") + "\n")
            return 1 if erreurs else 0
        print("\n  ✗ Liste non conforme : corrigez avant de mesurer (--verifier).\n")
        return 1

    sortie = args.exporter or f"releves-ia-{date.today():%Y-%m}{'-sans-web' if args.sans_web else ''}.csv"
    moteurs = moteurs_disponibles([m.strip() for m in args.moteurs.split(",") if m.strip()] or None, args.sans_web)
    if not moteurs:
        return grille_manuelle(prompts, sortie)
    concurrents = [c.strip() for c in args.concurrents.split(",") if c.strip()]

    if not args.json:
        mode = "sans web (notoriété)" if args.sans_web else "avec web (retrouvabilité)"
        print(f"\n  {len(prompts)} prompts × {', '.join(moteurs)} · {mode} · « {marque} » · {domaine}\n")
    releves, nb_erreurs = [], 0
    for moteur in moteurs:
        fonction = MOTEURS[moteur][1]
        for i, ligne in enumerate(prompts, 1):
            try:
                reponse = fonction(ligne["prompt"], web=not args.sans_web)
            except (ErreurMoteur, KeyError, IndexError) as exc:
                nb_erreurs += 1
                if not args.json:
                    print(f"  {moteur:<10} [{i:>2}] ✗ {str(exc)[:90]}")
                continue
            res = analyser(reponse, marque, domaine, concurrents)
            releves.append({"moteur": moteur, "famille": ligne["famille"], "funnel": ligne.get("funnel", ""),
                            "poids": ligne["poids"], "prompt": ligne["prompt"], **res})
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
    manquants = prompts_manquants(releves)
    sources = domaines_concurrents(releves, domaine)
    if args.json:
        print(json.dumps({"marque": marque, "domaine": domaine, "sans_web": args.sans_web, "moteurs": bilan,
                          "prompts_manquants": manquants, "sources_les_plus_citees": sources, "erreurs": nb_erreurs,
                          "releves": sortie}, ensure_ascii=False, indent=1))
        return 0 if releves else 1

    print(f"\n  {'Moteur':<11}{'mention':>9}{'pondéré':>9}{'SoV':>7}{'visibilité':>12}   (prompts sans la marque)")
    for moteur, m in bilan.items():
        sov = "—" if m["sov_pct"] is None else f"{m['sov_pct']:.0f}%"
        print(f"  {moteur:<11}{m['taux_mention_pct']:>8.1f}%{m['taux_mention_pondere_pct']:>8.1f}%{sov:>7}{m['visibilite']:>11.1f}")
    if manquants:
        print("\n  Prompts manquants (MOFU/BOFU, marque absente partout) :")
        for q in manquants[:10]:
            print(f"   - {q}")
    if sources:
        print("\n  Sources les plus citées à votre place :")
        for s, n in sources:
            print(f"    {n:>3} × {s}")
    print(f"\n  Relevés dans {sortie}. Refaites la mesure dans un mois, même liste, même mode.\n")
    return 0 if releves else 1


if __name__ == "__main__":
    sys.exit(main())
