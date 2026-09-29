#!/usr/bin/env python3
"""Score on-page /100 d'une page face à un mot-clé cible.

    python3 scripts/onpage_score.py https://exemple.com/page "mot clé cible"
    python3 scripts/onpage_score.py page.html "mot clé cible" --json
    python3 scripts/onpage_score.py page.html "pompe à chaleur" \
        --secondaires "pac air eau, prix pompe à chaleur" --url https://exemple.com/pompe-a-chaleur/ \
        --na "FAQ,Fraîcheur"

Barème : balises 20 · contenu 25 · lisibilité 15 · GEO 15 · E-E-A-T 15 ·
maillage 10. Chaque critère prend un feu : 🟢 = tous ses points, 🟡 = la
moitié arrondie au supérieur, 🔴 = 0, ⚪ = non applicable (ses points sont
redistribués au prorata dans sa catégorie, le score est « sous réserve »).
Puis un malus de sur-optimisation s'applique au score global, selon la
densité effective du mot-clé : max(densité exacte, densité distribuée).

Moteur de notation du skill seo-optimisation-onpage : il mesure, le skill
interprète et réécrit. Les fonctions de calcul sont pures et testées sans
réseau ni dépendance ; requests et bs4 ne servent qu'à lire la page.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

AGENT = "ClaudeCodeSEODecupler/2.0 (+https://decupler.com)"

VERT, JAUNE, ROUGE, NA = "🟢", "🟡", "🔴", "⚪"

# Mots vides retirés du mot-clé avant la correspondance distribuée : « prix
# d'une pompe à chaleur » et « pompe à chaleur : les prix » visent la même chose.
MOTS_VIDES = set("""
a au aux avec ce ces cet cette chez comme d dans de des du elle en et il ils
j l la le les leur leurs m ma mes mon n ne nos notre ou par pas pour qu que
qui s sa se ses son sur t ta te tes ton un une vos votre y est sont quel
quelle quels quelles comment pourquoi combien the of for and to in on an
""".split())

# Mots de liaison : un texte qui en manque se lit comme une liste de phrases
# posées côte à côte. Forme sans accents, en minuscules.
TRANSITIONS = [
    "d'abord", "tout d'abord", "ensuite", "puis", "enfin", "finalement", "premierement",
    "deuxiemement", "cependant", "pourtant", "toutefois", "neanmoins", "en revanche",
    "au contraire", "a l'inverse", "par ailleurs", "de plus", "en outre", "egalement",
    "aussi", "de meme", "ainsi", "donc", "par consequent", "c'est pourquoi", "si bien que",
    "des lors", "en effet", "car", "mais", "or", "par exemple", "notamment", "en particulier",
    "surtout", "autrement dit", "c'est-a-dire", "en resume", "bref", "en somme", "en bref",
    "d'une part", "d'autre part", "alors", "concretement", "en pratique", "afin de", "pour cela",
    "dans ce cas", "a condition", "meme si", "bien que", "tandis que", "alors que",
]
_TRANSITIONS = re.compile(r"(?<![\w'])(?:" + "|".join(re.escape(t) for t in TRANSITIONS) + r")(?![\w'])")

# Voix passive, heuristique française : une forme d'« être » suivie d'un
# participe passé. Les verbes conjugués avec « être » au passé composé
# (aller, venir…) et les pronominaux (s'est, se sont) sont exclus.
_ETRE = r"(?:est|sont|était|étaient|été|sera|seront|serait|seraient|soit|soient|fut|furent|être|suis|sommes|êtes)"
_ADVERBE = r"(?:(?:\w+ment|pas|plus|très|bien|déjà|souvent|toujours|aussi|jamais|parfois|ensuite)\s+)?"
_IRREGULIERS = (r"(?:fait|pris|mis|écrit|construit|produit|dit|conçu|vendu|rendu|reçu|tenu|obtenu|"
                r"ouvert|offert|couvert|soumis|permis|admis|inclus|remis|promis|compris|suivi|fourni|"
                r"choisi|réuni|défini|garanti|établi|connu|prévu|vu|lu)(?:e|s|es)?")
_PASSIF = re.compile(rf"(?<!s')(?<!s’)(?<!se )\b{_ETRE}\s+{_ADVERBE}(\w+(?:é|ée|és|ées)|{_IRREGULIERS})\b")
_ACTIFS_ETRE = {"allé", "allée", "allés", "allées", "arrivé", "arrivée", "arrivés", "arrivées", "né", "née",
                "nés", "nées", "parti", "tombé", "tombée", "resté", "restée", "restés", "devenu", "devenue",
                "entré", "entrée", "sorti", "monté", "descendu", "passé", "passée", "retourné", "rentré",
                "revenu", "venu", "venue", "apparu", "décédé"}

# Désignations vagues : un passage extrait par un moteur IA doit rester
# attribuable sans le reste de la page.
_VAGUES = re.compile(r"\b(?:notre|cette|la|votre) (?:solution|outil|plateforme|logiciel|produit|offre)\b|"
                     r"\b(?:la|notre|cette) (?:ville|région|commune)\b|\bnotre (?:société|entreprise|structure)\b",
                     re.I)

MOTS_FORTS = {"guide", "complet", "complete", "gratuit", "gratuite", "rapide", "facile", "meilleur",
              "meilleurs", "meilleure", "essentiel", "pratique", "simple", "efficace", "comparatif",
              "prix", "tarif", "tarifs", "avis", "devis", "etapes", "astuces", "erreurs", "conseils",
              "exemples", "definition", "pourquoi", "comment", "officiel", "certifie", "nouveau"}

ANCRES_VIDES = {"", "cliquez ici", "ici", "en savoir plus", "lire la suite", "voir", "voir plus",
                "lien", "cet article", "plus", "découvrir", "suite", "cliquez", "this", "here", "read more"}

POURQUOI = {
    "Title": "C'est le premier signal de pertinence et la ligne cliquable de la SERP.",
    "Title accrocheur": "Un chiffre ou un mot fort distingue le résultat des neuf autres et relève le CTR.",
    "Longueur de la meta": "Entre 120 et 156 caractères, la description s'affiche entière sur mobile comme sur ordinateur.",
    "Mot-clé dans la meta": "Google met en gras les termes recherchés : la meta qui les contient attire l'œil.",
    "H1": "Le H1 annonce le sujet au lecteur et aux moteurs ; deux H1 brouillent le message.",
    "Hiérarchie Hn": "Les moteurs et les IA découpent la page par ses titres : un saut de niveau casse le plan.",
    "Mot-clé dans le slug": "L'URL s'affiche dans la SERP et reste un signal de pertinence, stable dans le temps.",
    "Mot-clé dans les zones clés": "Le H1, l'ouverture, un H2 et la conclusion sont les zones que les moteurs pondèrent.",
    "Densité": "Trop peu, le sujet est flou ; trop, le texte sent le bourrage et le lecteur décroche.",
    "Mot-clé dans un alt": "L'alt rattache les images au sujet et alimente la recherche d'images.",
    "Mots-clés secondaires": "Les variantes couvrent les requêtes voisines sans créer une page par formulation.",
    "Richesse sémantique": "Un vocabulaire varié signale une couverture réelle du sujet, pas une répétition.",
    "Profondeur": "Un contenu mince ne répond pas à toutes les questions que le top 3 traite.",
    "Originalité et preuves": "Chiffres, tableaux et listes sont ce que les moteurs et les IA reprennent et citent.",
    "Clarté des entités": "« Notre solution » ne veut rien dire hors contexte : un passage cité doit nommer ce dont il parle.",
    "Fréquence des intertitres": "Un bloc de plus de 500 mots sans titre ne se parcourt pas et ne se découpe pas.",
    "Phrases longues": "Au-delà de 20 mots, une phrase se relit ; au-delà d'un tiers du texte, on abandonne.",
    "Longueur des paragraphes": "Un paragraphe de plus de 150 mots devient un mur sur mobile.",
    "Mots de transition": "Les liaisons montrent le raisonnement ; sans elles, le texte est une liste déguisée.",
    "Voix passive": "La voix active dit qui fait quoi : plus direct, plus court, plus citable.",
    "Réponse directe": "Les IA et les extraits optimisés reprennent le paragraphe qui répond seul, en tête.",
    "Structure extractible": "Listes et tableaux s'extraient tels quels dans les réponses générées.",
    "Définitions autonomes": "Une définition en une phrase est le format le plus cité par les moteurs IA.",
    "FAQ": "Les questions du lecteur, formulées comme il les tape, couvrent la longue traîne et les PAA.",
    "Données sourcées": "Un chiffre sans source n'est ni vérifiable ni citable.",
    "Auteur identifié": "On cite ce qu'on peut attribuer à quelqu'un d'identifiable.",
    "Expérience de première main": "L'expérience vécue est le signal E-E-A-T le plus discriminant.",
    "Sources externes": "Lier les sources d'autorité montre qu'on s'appuie sur plus que son avis.",
    "Fraîcheur": "Une date de mise à jour récente rassure le lecteur et oriente les moteurs sur les sujets qui bougent.",
    "Transparence": "Contact, mentions légales, à propos : les preuves qu'il y a quelqu'un derrière la page.",
    "Liens internes": "Les liens internes transmettent l'autorité et guident vers la page suivante.",
    "Ancres descriptives": "« Cliquez ici » ne dit rien de la page cible, ni au lecteur ni au moteur.",
    "Liens externes": "Un lien sortant pertinent inscrit la page dans son écosystème.",
    "Images": "Sans alt, une image est muette pour les moteurs et les lecteurs d'écran.",
    "Schema JSON-LD": "Le balisage dit aux machines ce qu'est la page, sans ambiguïté.",
}

BLOCS = {"A": ("Balises et structure", 20), "B": ("Contenu et sémantique", 25),
         "C": ("Lisibilité", 15), "D": ("GEO et citabilité", 15),
         "E": ("E-E-A-T", 15), "F": ("Maillage et technique", 10)}


# ─── Texte ────────────────────────────────────────────────────────

def sans_accents(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte.lower().replace("’", "'"))
                   if unicodedata.category(c) != "Mn")


def contient(texte: str, cle: str) -> bool:
    """Comparaison tolérante aux accents et à la casse."""
    return sans_accents(cle) in sans_accents(texte)


def racine(mot: str) -> str:
    """Singulier approximatif : « pompes » et « pompe » comptent pour un."""
    return mot[:-1] if len(mot) > 3 and mot[-1] in "sx" else mot


def jetons(texte: str) -> list[str]:
    return [racine(m) for m in re.findall(r"[a-z0-9]+", sans_accents(texte))]


def mots_utiles(cle: str) -> list[str]:
    tous = jetons(cle)
    return [m for m in tous if m not in MOTS_VIDES] or tous


def occurrences_exactes(tokens: list[str], cle: str) -> int:
    k = jetons(cle)
    if not k:
        return 0
    return sum(1 for i in range(len(tokens) - len(k) + 1) if tokens[i:i + len(k)] == k)


def occurrences_distribuees(tokens: list[str], cle: str) -> int:
    """Tous les mots utiles dans une fenêtre de (mots utiles + 4) mots.

    Une fenêtre comptée n'est plus réexaminée : deux mots-clés collés ne
    comptent pas trois fois.
    """
    utiles = mots_utiles(cle)
    if not utiles:
        return 0
    cibles, largeur = set(utiles), len(utiles) + 4
    n = i = 0
    while i < len(tokens):
        if tokens[i] in cibles and cibles <= set(tokens[i:i + largeur]):
            n += 1
            i += largeur
        else:
            i += 1
    return n


def densites(texte: str, cle: str) -> dict:
    tokens = jetons(texte)
    total = len(tokens)
    exactes, distribuees = occurrences_exactes(tokens, cle), occurrences_distribuees(tokens, cle)
    d_ex = exactes / total * 100 if total else 0.0
    d_di = distribuees / total * 100 if total else 0.0
    return {"mots": total, "occurrences_exactes": exactes, "occurrences_distribuees": distribuees,
            "exacte": round(d_ex, 2), "distribuee": round(d_di, 2), "effective": round(max(d_ex, d_di), 2)}


def trouve(texte: str, cle: str) -> bool:
    tokens = jetons(texte)
    return occurrences_exactes(tokens, cle) > 0 or occurrences_distribuees(tokens, cle) > 0


def presence(texte: str, cle: str) -> str:
    """Pour un champ court (title, H1, meta, slug, alt) : exact, complet, variante ou absent."""
    tokens = jetons(texte)
    if occurrences_exactes(tokens, cle):
        return "exact"
    utiles = mots_utiles(cle)
    trouves = sum(1 for m in set(utiles) if m in tokens)
    if utiles and trouves == len(set(utiles)):
        return "complet"
    return "variante" if utiles and trouves * 2 >= len(set(utiles)) else "absent"


# ─── Barème (pur) ─────────────────────────────────────────────────

def malus(densite: float) -> int:
    """Malus de sur-optimisation retiré du score global."""
    if densite <= 3.5:
        return 0
    if densite <= 5:
        return 5
    if densite <= 6.5:
        return 8
    return 12


def feu_densite(d: float) -> str:
    if 0.5 <= d <= 2.5:
        return VERT
    if 2.5 < d <= 3.5 or 0.3 <= d < 0.5:
        return JAUNE
    return ROUGE


def points(feu: str, maxi: int) -> int:
    return maxi if feu == VERT else math.ceil(maxi / 2) if feu == JAUNE else 0


def score_bloc(criteres: list[dict], maxi: int) -> tuple[int | None, bool]:
    """Score d'une catégorie ; les ⚪ sont retirés et leurs points redistribués."""
    applicables = [c for c in criteres if c["feu"] != NA]
    sous_reserve = len(applicables) < len(criteres)
    possible = sum(c["max"] for c in applicables)
    if not possible:
        return None, True
    return round(sum(c["points"] for c in applicables) * maxi / possible), sous_reserve


def bande(score: int) -> str:
    return VERT if score >= 80 else JAUNE if score >= 55 else ROUGE


def feu_ratio(obtenu: float, maxi: float) -> str:
    return bande(round(obtenu / maxi * 100)) if maxi else NA


def decouper_phrases(blocs: list[str]) -> list[str]:
    phrases = []
    for b in blocs:
        phrases += [p.strip() for p in re.split(r"[.!?…]+(?=\s|$)", b) if p.strip() and p.split()]
    return phrases


def pct_phrases_longues(phrases: list[str], seuil: int = 20) -> float:
    return round(sum(1 for p in phrases if len(p.split()) > seuil) / len(phrases) * 100, 1) if phrases else 0.0


def pct_transitions(phrases: list[str]) -> float:
    return round(sum(1 for p in phrases if _TRANSITIONS.search(sans_accents(p))) / len(phrases) * 100, 1) \
        if phrases else 0.0


def est_passive(phrase: str) -> bool:
    return any(m.group(1) not in _ACTIFS_ETRE for m in _PASSIF.finditer(phrase.lower().replace("’", "'")))


def pct_passif(phrases: list[str]) -> float:
    return round(sum(1 for p in phrases if est_passive(p)) / len(phrases) * 100, 1) if phrases else 0.0


MOIS = {m: i for i, m in enumerate(["janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet",
                                     "aout", "septembre", "octobre", "novembre", "decembre"], 1)}


def dates_trouvees(textes: list[str]) -> list[dt.date]:
    dates = []
    for t in textes:
        s = sans_accents(t)
        for a, m, j in re.findall(r"\b((?:19|20)\d\d)-(\d\d)-(\d\d)", s):
            dates.append((int(a), int(m), int(j)))
        for j, m, a in re.findall(r"(?:mis|mise) a jour[^0-9]{0,15}(\d{1,2})[/.](\d{1,2})[/.]((?:19|20)\d\d)", s):
            dates.append((int(a), int(m), int(j)))
        for j, m, a in re.findall(r"\b(\d{1,2}) (" + "|".join(MOIS) + r") ((?:19|20)\d\d)", s):
            dates.append((int(a), MOIS[m], int(j)))
    valides = []
    for a, m, j in dates:
        try:
            valides.append(dt.date(a, m, j))
        except ValueError:
            pass
    return valides


def feu_fraicheur(dates: list[dt.date], aujourdhui: dt.date) -> tuple[str, str]:
    passees = [d for d in dates if d <= aujourdhui]
    if not passees:
        return ROUGE, "aucune date détectée"
    recente = max(passees)
    age = (aujourdhui - recente).days
    return (VERT if age <= 365 else JAUNE), f"date la plus récente : {recente.isoformat()} ({age} j)"


def normaliser_nom(nom: str) -> str:
    return sans_accents(nom).strip()


# ─── Notation ─────────────────────────────────────────────────────

def charger(source: str) -> str:
    chemin = Path(source)
    if chemin.exists():
        return chemin.read_text(encoding="utf-8")
    import requests
    rep = requests.get(source, headers={"User-Agent": AGENT}, timeout=30)
    rep.raise_for_status()
    return rep.text


def noter(html: str, cle: str, secondaires: list[str] | None = None, url: str | None = None,
          na: list[str] | None = None, aujourdhui: dt.date | None = None) -> dict:
    from bs4 import BeautifulSoup

    aujourdhui = aujourdhui or dt.date.today()
    soup = BeautifulSoup(html, "html.parser")
    criteres: list[dict] = []

    def ajouter(bloc, nom, maxi, feu, constat):
        criteres.append({"bloc": bloc, "critere": nom, "points": points(feu, maxi), "max": maxi,
                         "feu": feu, "constat": constat, "pourquoi": POURQUOI.get(nom, "")})

    # Une page collée sans <head> ne dit rien de ses balises : c'est une
    # information non fournie (⚪), pas une optimisation ratée (🔴).
    tete_fournie = soup.find("head") is not None or soup.title is not None

    # ── A · Balises et structure (20) ───────────────────────────────
    title = (soup.title.get_text() or "").strip() if soup.title else ""
    if not tete_fournie:
        ajouter("A", "Title", 5, NA, "non fourni")
        ajouter("A", "Title accrocheur", 1, NA, "non fourni")
    elif not title:
        ajouter("A", "Title", 5, ROUGE, "absent")
        ajouter("A", "Title accrocheur", 1, ROUGE, "absent")
    else:
        pres = presence(title, cle)
        tot = mots_utiles(cle)
        tot_debut = jetons(title)[:4]
        tot_tot = any(m in tot_debut for m in tot)
        longueur_ok = 50 <= len(title) <= 60
        feu = (VERT if pres in ("exact", "complet") and tot_tot and longueur_ok
               else ROUGE if pres == "absent" else JAUNE)
        ajouter("A", "Title", 5, feu, f"« {title} » — {len(title)} car., mot-clé {pres}"
                + ("" if tot_tot or pres == "absent" else ", tardif"))
        fort = bool(re.search(r"\d", title)) or bool(set(re.findall(r"[a-z]+", sans_accents(title))) & MOTS_FORTS)
        ajouter("A", "Title accrocheur", 1, VERT if fort else JAUNE,
                "chiffre ou mot fort présent" if fort else "ni chiffre ni mot fort")

    tag = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    meta = (tag.get("content") or "").strip() if tag else ""
    if not tete_fournie:
        ajouter("A", "Longueur de la meta", 2, NA, "non fournie")
        ajouter("A", "Mot-clé dans la meta", 2, NA, "non fournie")
    elif not meta:
        ajouter("A", "Longueur de la meta", 2, ROUGE, "absente")
        ajouter("A", "Mot-clé dans la meta", 2, ROUGE, "meta absente")
    else:
        n = len(meta)
        ajouter("A", "Longueur de la meta", 2,
                VERT if 120 <= n <= 156 else JAUNE if 100 <= n <= 170 else ROUGE, f"{n} car. (cible 120-156)")
        pres = presence(meta, cle)
        ajouter("A", "Mot-clé dans la meta", 2,
                VERT if pres in ("exact", "complet") else JAUNE if pres == "variante" else ROUGE, f"mot-clé {pres}")

    h1s = soup.find_all("h1")
    if not h1s:
        ajouter("A", "H1", 4, ROUGE, "absent")
    else:
        pres = presence(h1s[0].get_text(" ", strip=True), cle)
        bon = pres in ("exact", "complet")
        if len(h1s) > 1:
            ajouter("A", "H1", 4, JAUNE if bon else ROUGE, f"{len(h1s)} H1 — il n'en faut qu'un")
        else:
            ajouter("A", "H1", 4, VERT if bon else JAUNE if pres == "variante" else ROUGE, f"unique, mot-clé {pres}")

    niveaux = [int(t.name[1]) for t in soup.find_all(re.compile("^h[1-6]$"))]
    sauts = sum(1 for a, b in zip(niveaux, niveaux[1:]) if b - a > 1)
    feu = VERT if not sauts and len(niveaux) >= 3 else JAUNE if sauts <= 1 and niveaux else ROUGE
    ajouter("A", "Hiérarchie Hn", 3, feu, f"{len(niveaux)} titres, {sauts} saut(s) de niveau")

    canonical = soup.find("link", attrs={"rel": re.compile("canonical", re.I)})
    adresse = (canonical.get("href", "") if canonical else "") or url or ""
    if not adresse:
        ajouter("A", "Mot-clé dans le slug", 3, NA, "URL inconnue (ni canonical ni --url)")
    else:
        chemin = urlparse(adresse).path or adresse
        tokens_slug = jetons(chemin.replace("-", " ").replace("_", " ").replace("/", " "))
        # Tous les mots utiles, pas seulement le premier : « prix pompe à
        # chaleur » sur /pompe-a-chaleur/ perd le mot qui porte l'intention.
        bruts = [m for m in re.findall(r"[a-z0-9]+", sans_accents(cle)) if m not in MOTS_VIDES] \
            or re.findall(r"[a-z0-9]+", sans_accents(cle))
        utiles = list(dict.fromkeys(bruts))
        manquants = [m for m in utiles if racine(m) not in tokens_slug]
        feu = VERT if not manquants else JAUNE if len(manquants) < len(utiles) else ROUGE
        ajouter("A", "Mot-clé dans le slug", 3, feu,
                f"{chemin}" + (f" — manque : {', '.join(manquants)}" if manquants else " — tous les mots utiles"))

    # ── Extraction du contenu principal ─────────────────────────────
    # Le JSON-LD est lu AVANT de retirer les <script> : sinon il disparaît
    # et le bloc F le compte à tort comme absent.
    jsonld = " ".join(s.get_text() for s in soup.find_all("script", attrs={"type": "application/ld+json"}))
    dates_meta = [m.get("content", "") for m in soup.find_all("meta", attrs={"property": re.compile("time$")})]
    dates_time = [t.get("datetime", "") or t.get_text() for t in soup.find_all("time")]
    images = soup.find_all("img")
    alts = [(i.get("alt") or "").strip() for i in images]

    for balise in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        balise.decompose()
    texte = soup.get_text(" ", strip=True)
    mots = texte.split()
    nb_mots = len(mots)
    dens = densites(texte, cle)

    # ── B · Contenu et sémantique (25) ──────────────────────────────
    zones = {"H1": bool(h1s) and presence(h1s[0].get_text(" "), cle) in ("exact", "complet"),
             "100 premiers mots": trouve(" ".join(mots[:100]), cle),
             "un H2": any(presence(h.get_text(" "), cle) in ("exact", "complet") for h in soup.find_all("h2")),
             "conclusion": trouve(" ".join(mots[-150:]), cle)}
    couvertes = sum(zones.values())
    manquantes = [z for z, ok in zones.items() if not ok]
    ajouter("B", "Mot-clé dans les zones clés", 5, VERT if couvertes == 4 else JAUNE if couvertes >= 2 else ROUGE,
            f"{couvertes}/4" + (f" — manque : {', '.join(manquantes)}" if manquantes else ""))

    ajouter("B", "Densité", 3, feu_densite(dens["effective"]),
            f"effective {dens['effective']} % (exacte {dens['exacte']} %, distribuée {dens['distribuee']} %) "
            f"— cible 0,5-2,5 %")

    if not images:
        ajouter("B", "Mot-clé dans un alt", 2, NA, "aucune image")
    else:
        rangs = {"exact": 3, "complet": 3, "variante": 1, "absent": 0}
        meilleur = max((rangs[presence(a, cle)] for a in alts if a), default=0)
        ajouter("B", "Mot-clé dans un alt", 2, VERT if meilleur == 3 else JAUNE if meilleur else ROUGE,
                f"{len(images)} image(s), meilleur alt : "
                + {3: "mot-clé", 1: "variante", 0: "sans mot-clé"}[meilleur])

    if not secondaires:
        ajouter("B", "Mots-clés secondaires", 3, NA, "non fournis (--secondaires)")
    else:
        presents = [s for s in secondaires if trouve(texte, s)]
        pic = max((densites(texte, s)["effective"] for s in secondaires), default=0)
        absents = [s for s in secondaires if s not in presents]
        feu = (VERT if not absents and pic <= 2.5
               else JAUNE if len(presents) * 2 >= len(secondaires) and pic <= 3.5 else ROUGE)
        ajouter("B", "Mots-clés secondaires", 3, feu, f"{len(presents)}/{len(secondaires)} présents, densité max "
                f"{pic} %" + (f" — absents : {', '.join(absents)}" if absents else ""))

    termes = set(re.findall(r"\b[a-zà-ÿ]{5,}\b", texte.lower()))
    ajouter("B", "Richesse sémantique", 4, VERT if len(termes) > 300 else JAUNE if len(termes) > 150 else ROUGE,
            f"{len(termes)} termes distincts")

    ajouter("B", "Profondeur", 4, VERT if nb_mots >= 1000 else JAUNE if nb_mots >= 500 else ROUGE,
            f"{nb_mots} mots (seuil indicatif : comparer au top 3)")

    a_tableau = bool(soup.find("table"))
    a_liste = len(soup.find_all(["ul", "ol"])) >= 2
    # Pas de \b final : un symbole comme € ou % n'est pas un caractère de mot,
    # donc \b après lui ne se déclenche jamais et la détection échouerait.
    nb_chiffres = len(re.findall(r"\d+(?:[  .,]\d+)*\s*(?:%|€|\$|k€|ans?\b|jours?\b|heures?\b|min\b|mois\b)",
                                 texte, re.I))
    feu = VERT if nb_chiffres >= 3 and (a_tableau or a_liste) else JAUNE if nb_chiffres or a_tableau else ROUGE
    ajouter("B", "Originalité et preuves", 2, feu, f"{nb_chiffres} donnée(s) chiffrée(s) · tableau "
            f"{'oui' if a_tableau else 'non'} · listes {'oui' if a_liste else 'non'}")

    vagues = _VAGUES.findall(texte)
    ajouter("B", "Clarté des entités", 2, VERT if not vagues else JAUNE if len(vagues) <= 2 else ROUGE,
            f"{len(vagues)} désignation(s) vague(s)" + (f" : {', '.join(sorted(set(v.lower() for v in vagues))[:4])}"
                                                       if vagues else ""))

    # ── C · Lisibilité (15) ─────────────────────────────────────────
    blocs_titres, courant = [], 0
    for s in soup.find_all(string=True):
        if s.find_parent(re.compile("^h[1-6]$")):
            blocs_titres.append(courant)
            courant = 0
        else:
            courant += len(str(s).split())
    blocs_titres.append(courant)
    intertitres = len(soup.find_all(["h2", "h3"]))
    plus_long = max(blocs_titres)
    ratio = nb_mots / intertitres if intertitres else nb_mots
    feu = ROUGE if plus_long > 500 else VERT if ratio <= 300 else JAUNE
    ajouter("C", "Fréquence des intertitres", 3, feu,
            f"{intertitres} H2/H3, 1 pour {round(ratio)} mots, plus long bloc sans titre : {plus_long} mots")

    blocs_texte = [b.get_text(" ", strip=True) for b in soup.find_all(["p", "li", "blockquote", "td", "dd"])]
    phrases = decouper_phrases(blocs_texte or [texte])
    longues = pct_phrases_longues(phrases)
    ajouter("C", "Phrases longues", 3, VERT if longues < 25 else JAUNE if longues <= 35 else ROUGE,
            f"{longues} % de phrases de plus de 20 mots")

    paragraphes = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    if not paragraphes:
        ajouter("C", "Longueur des paragraphes", 3, NA, "aucun paragraphe <p>")
    else:
        tailles = [len(p.split()) for p in paragraphes]
        au_dela = sum(1 for t in tailles if t > 200)
        ajouter("C", "Longueur des paragraphes", 3,
                ROUGE if au_dela >= 2 else JAUNE if max(tailles) > 150 else VERT,
                f"plus long : {max(tailles)} mots, {au_dela} au-delà de 200")

    trans = pct_transitions(phrases)
    ajouter("C", "Mots de transition", 3, VERT if trans >= 30 else JAUNE if trans >= 20 else ROUGE,
            f"{trans} % des phrases")

    passif = pct_passif(phrases)
    ajouter("C", "Voix passive", 3, VERT if passif < 10 else JAUNE if passif <= 20 else ROUGE,
            f"{passif} % des phrases (heuristique)")

    # ── D · GEO et citabilité (15) ──────────────────────────────────
    reponse = next((p for p in paragraphes[:4] if 30 <= len(p.split()) <= 90), "")
    ajouter("D", "Réponse directe", 5,
            VERT if reponse else JAUNE if paragraphes and len(paragraphes[0].split()) >= 20 else ROUGE,
            f"{len(reponse.split())} mots en tête" if reponse else "aucun paragraphe de 40-60 mots en ouverture")

    structures = len(soup.find_all(["ul", "ol", "table"]))
    ajouter("D", "Structure extractible", 3, VERT if structures >= 3 else JAUNE if structures else ROUGE,
            f"{structures} liste(s) ou tableau(x)")

    definitions = len(re.findall(r"\b(est un|est une|désigne|consiste à|se définit)\b", texte, re.I))
    ajouter("D", "Définitions autonomes", 2, VERT if definitions >= 2 else JAUNE if definitions else ROUGE,
            f"{definitions} formulation(s) de définition")

    a_faq = bool(soup.find(string=re.compile(r"FAQ|questions fréquentes", re.I))) or bool(soup.find_all("details"))
    ajouter("D", "FAQ", 3, VERT if a_faq else ROUGE, "présente" if a_faq else "absente")

    liens = [a for a in soup.find_all("a", href=True)]
    hote = urlparse(adresse).netloc if adresse.startswith("http") else ""
    externes = [a for a in liens if a["href"].startswith("http") and (not hote or urlparse(a["href"]).netloc != hote)]
    internes = [a for a in liens if a not in externes and not a["href"].startswith(("#", "mailto:", "tel:"))]
    feu = VERT if nb_chiffres and len(externes) >= 2 else JAUNE if nb_chiffres and externes else ROUGE
    ajouter("D", "Données sourcées", 2, feu, f"{nb_chiffres} chiffre(s), {len(externes)} lien(s) sortant(s)")

    # ── E · E-E-A-T (15) ────────────────────────────────────────────
    a_auteur = bool(re.search(r"\b(par|rédigé par|auteur|author)\b", texte[:2000], re.I)) or '"Person"' in jsonld
    ajouter("E", "Auteur identifié", 4, VERT if a_auteur else ROUGE,
            "signature détectée" if a_auteur else "aucune signature")

    experience = len(re.findall(r"\b(nous avons|j'ai|notre expérience|sur \d+|nos \d+|testé|constaté|observé)\b",
                                texte, re.I))
    ajouter("E", "Expérience de première main", 4, VERT if experience >= 3 else JAUNE if experience else ROUGE,
            f"{experience} marqueur(s)")

    ajouter("E", "Sources externes", 2, VERT if len(externes) >= 3 else JAUNE if externes else ROUGE,
            f"{len(externes)} lien(s) sortant(s)")

    feu, constat = feu_fraicheur(dates_trouvees([jsonld, *dates_meta, *dates_time, texte]), aujourdhui)
    ajouter("E", "Fraîcheur", 3, feu, constat)

    a_confiance = bool(re.search(r"\b(contact|mentions légales|à propos)\b", html, re.I))
    ajouter("E", "Transparence", 2, VERT if a_confiance else ROUGE,
            "liens de confiance présents" if a_confiance else "aucun")

    # ── F · Maillage et technique (10) ──────────────────────────────
    ajouter("F", "Liens internes", 3, VERT if len(internes) >= 3 else JAUNE if internes else ROUGE,
            f"{len(internes)} lien(s) interne(s) dans le contenu")

    if not liens:
        ajouter("F", "Ancres descriptives", 2, NA, "aucun lien dans le contenu")
    else:
        vides = [a.get_text(" ", strip=True) for a in liens
                 if a.get_text(" ", strip=True).lower() in ANCRES_VIDES or a.get_text(strip=True).startswith("http")]
        part = len(vides) / len(liens)
        ajouter("F", "Ancres descriptives", 2, VERT if not vides else JAUNE if part <= 0.2 else ROUGE,
                f"{len(vides)}/{len(liens)} ancre(s) génériques")

    ajouter("F", "Liens externes", 1, VERT if externes else ROUGE, f"{len(externes)} lien(s)")

    sans_alt = sum(1 for a in alts if not a)
    ajouter("F", "Images", 2, (VERT if not sans_alt else JAUNE if sans_alt < len(images) else ROUGE) if images else ROUGE,
            f"{len(images)} image(s), {sans_alt} sans alt" if images else "aucune image")

    ajouter("F", "Schema JSON-LD", 2, VERT if jsonld.strip() else ROUGE, "présent" if jsonld.strip() else "absent")

    # ── Non applicables déclarés ────────────────────────────────────
    declares = {normaliser_nom(n) for n in (na or []) if n.strip()}
    for c in criteres:
        if normaliser_nom(c["critere"]) in declares:
            c.update(feu=NA, points=0, constat=c["constat"] + " — déclaré non applicable")

    return agreger(criteres, dens, nb_mots)


def agreger(criteres: list[dict], dens: dict, nb_mots: int) -> dict:
    blocs, total, possible = {}, 0, 0
    for lettre, (_, maxi) in BLOCS.items():
        score, reserve = score_bloc([c for c in criteres if c["bloc"] == lettre], maxi)
        blocs[lettre] = {"points": score if score is not None else 0, "max": maxi, "sous_reserve": reserve}
        if score is not None:
            total += score
            possible += maxi
    brut = round(total * 100 / possible) if possible else 0
    m = malus(dens["effective"])
    final = max(0, brut - m)
    return {"score": final, "score_brut": brut, "malus": m, "bande": bande(final),
            "sous_reserve": any(b["sous_reserve"] for b in blocs.values()),
            "densite": dens, "criteres": criteres, "blocs": blocs, "mots": nb_mots}


def afficher(res: dict, cle: str) -> None:
    score, brut, m = res["score"], res["score_brut"], res["malus"]
    reserve = "  (sous réserve : critères ⚪ non applicables)" if res["sous_reserve"] else ""
    ligne = f"{brut}, −{m} → {score}/100" if m else f"{score}/100"

    print(f"\n{'═' * 66}")
    print(f"  SCORE ON-PAGE : {ligne}   {res['bande']}{reserve}")
    print(f"  Mot-clé cible : « {cle} »   ·   {res['mots']} mots")
    if m:
        print(f"  Malus de sur-optimisation : densité effective {res['densite']['effective']} % → −{m}")
    print(f"{'═' * 66}\n")

    for lettre, (nom, _) in BLOCS.items():
        b = res["blocs"][lettre]
        print(f"  {lettre} · {nom:<24} {b['points']:>2}/{b['max']:<3} {feu_ratio(b['points'], b['max'])}"
              + ("  sous réserve" if b["sous_reserve"] else ""))
    print()

    a_corriger = [c for c in res["criteres"] if c["feu"] in (JAUNE, ROUGE)]
    if a_corriger:
        print("─── À corriger, par priorité ───\n")
        for c in sorted(a_corriger, key=lambda x: (x["feu"] != ROUGE, -x["max"])):
            print(f"  {c['feu']} {c['critere']} — {c['points']}/{c['max']}")
            print(f"     {c['constat']}")
            print(f"     Pourquoi ça compte : {c['pourquoi']}\n")
    else:
        print("  Tous les critères applicables sont au vert.\n")
    na = [c["critere"] for c in res["criteres"] if c["feu"] == NA]
    if na:
        print(f"  ⚪ Non applicables : {', '.join(na)}\n")


def main() -> int:
    p = argparse.ArgumentParser(description="Score on-page /100")
    p.add_argument("source", help="URL ou fichier HTML")
    p.add_argument("motcle", help="mot-clé cible")
    p.add_argument("--secondaires", help="mots-clés secondaires séparés par des virgules")
    p.add_argument("--url", help="URL de la page, pour le slug, si le fichier n'a pas de canonical")
    p.add_argument("--na", help="critères non applicables, séparés par des virgules (ex. \"FAQ,Fraîcheur\")")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    try:
        import bs4  # noqa: F401
    except ImportError:
        print("Dépendances manquantes. Lancez : pip install -r requirements.txt", file=sys.stderr)
        return 1

    secondaires = [s.strip() for s in (args.secondaires or "").split(",") if s.strip()]
    url = args.url or (args.source if args.source.startswith("http") else None)
    na = (args.na or "").split(",")
    res = noter(charger(args.source), args.motcle, secondaires, url, na)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        afficher(res, args.motcle)
    return 0


if __name__ == "__main__":
    sys.exit(main())
