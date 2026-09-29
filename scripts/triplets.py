#!/usr/bin/env python3
"""Triplets sémantiques, entités et cohérence des faits d'un site.

    python3 scripts/triplets.py extraire page.html                 # ce que la page affirme
    python3 scripts/triplets.py extraire https://exemple.com/page/
    python3 scripts/triplets.py extraire --texte "Atlas Conseil est un cabinet…"
    python3 scripts/triplets.py verifier page.html --page /bilan-annuel/ --strict
    python3 scripts/triplets.py coherence contenus/ [--triplets memoire/triplets.csv]
    python3 scripts/triplets.py jsonld --about "Atlas Conseil" --depuis page.html --url https://exemple.com/page/
    python3 scripts/triplets.py wikidata "Expertise comptable" [--site exemple.com]

Un triplet, c'est une connaissance réduite à sa forme la plus simple :
sujet — prédicat — objet (« Atlas Conseil — est situé à — Lyon »). Une page
qui énonce ses faits clés sous cette forme, une idée par phrase, sujet nommé,
se laisse extraire et citer par un moteur IA. Le script :

- `extraire`  : relève les triplets candidats d'une page (heuristiques FR/EN :
  copule, définition, « permet de », prix, durée, chiffres avec unité, dates)
  et les entités de son JSON-LD (about, mentions, sameAs) ;
- `verifier`  : confronte une page au registre du projet
  (`memoire/entites.csv`, `memoire/triplets.csv`) : triplets requis affirmés
  ou non, entités sans sameAs/QID, saillance, taux de couverture ;
- `coherence` : sur un dossier de contenus ou une liste d'URL, trouve un même
  sujet + prédicat avec des valeurs différentes (contradictions) ;
- `jsonld`    : produit le fragment about/mentions (ou knowsAbout) depuis le
  registre, avec les sameAs Wikidata, à fusionner dans le graphe de la page ;
- `wikidata`  : cherche le QID d'un libellé (API publique, sans clé).

Bibliothèque standard uniquement. Les fonctions de calcul sont pures : les
tests les exercent sur des fragments écrits à la main, sans réseau.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schema_validate import analyser_html, liste, parcourir, types_de  # noqa: E402

TETE_MOTS = 200          # « près du haut » : les faits clés tiennent dans les 200 premiers mots
MAX_ABOUT, MAX_MENTIONS = 3, 12
EXTENSIONS = {".html", ".htm", ".md", ".markdown", ".json", ".txt"}
AGENT = "seo-triplets/1.0 (outil SEO libre ; script triplets.py)"

# ─── Normalisation ────────────────────────────────────────────────

DETERMINANTS = re.compile(
    r"^(?:(?:l'|d'|de l'|(?:le|la|les|un|une|des|du|de la|ce|cet|cette|ces|son|sa|ses|leur|leurs|notre|nos|"
    r"votre|vos|the|a|an|this|these|our|your)(?:\s+|$))\s*)+")
PRONOMS = {"il", "elle", "ils", "elles", "on", "cela", "ca", "ce", "ceci", "c'", "celui-ci", "celle-ci",
           "ce dernier", "cette derniere", "ces derniers", "celui", "celle", "it", "they", "this", "that",
           "these", "those", "we", "nous", "vous", "you", "he", "she", "lui", "eux"}
DEMONSTRATIFS = {"ce", "cet", "cette", "ces"}
# Sujets trop généraux pour comparer deux pages : « le prix » d'une page n'est pas celui de l'autre.
SUJETS_VAGUES = {"prix", "cout", "tarif", "tarifs", "delai", "duree", "montant", "total", "budget", "taux",
                 "frais", "offre", "service", "prestation", "formule", "price", "cost", "fee", "rate"}
MOTS_VIDES = set("""
a au aux avec ce ces dans de des du en et la le les leur leurs l d un une ou par pour sur se sa son ses
qui que quoi dont est sont the of and to in on for is are be with by an or as at from this that it
""".split())
_JETON = re.compile(r"[^\W_]+(?:'[^\W_]+)?")


def sans_accents(texte: str) -> str:
    t = unicodedata.normalize("NFD", (texte or "").lower().replace("’", "'").replace("\u00a0", " "))
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def norm(texte: str) -> str:
    """Minuscules, sans accents, espaces et ponctuation de bord réduits."""
    return re.sub(r"\s+", " ", sans_accents(texte)).strip(" .,;:!?«»\"()[]—–-")


def cle_sujet(sujet: str) -> str:
    """La forme comparable d'un sujet : sans déterminant ni ponctuation."""
    return DETERMINANTS.sub("", norm(sujet)).strip()


def jetons(texte: str) -> list[str]:
    return [j for j in _JETON.findall(sans_accents(texte)) if j not in MOTS_VIDES and len(j) > 1]


def radicaux(texte: str) -> set[str]:
    """Radical grossier (5 lettres) : « classe », « classent », « classement » se rejoignent."""
    return {j[:5] for j in jetons(texte)}


def contient(texte_norm: str, terme: str) -> int:
    """Nombre d'occurrences de `terme` (normalisé) en mots entiers dans un texte normalisé."""
    t = norm(terme)
    if not t:
        return 0
    return len(re.findall(rf"(?<![\w]){re.escape(t)}(?![\w])", texte_norm))


def decouper_phrases(texte: str) -> list[str]:
    morceaux = re.split(r"(?<=[.!?…])[\"»”)]*\s+(?=[\"«“(]?[A-ZÀ-ÖØ-Þ0-9])", (texte or "").strip())
    return [m.strip() for m in morceaux if re.search(r"\w", m)]


# ─── Quantités : nombres, unités, monnaies, pourcentages, dates ──

MOIS = {"janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7, "aout": 8,
        "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12, "january": 1, "february": 2,
        "march": 3, "april": 4, "may": 5, "june": 6, "july": 7, "august": 8, "september": 9,
        "october": 10, "november": 11, "december": 12}
NOMBRES_MOTS = {"un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7,
                "huit": 8, "neuf": 9, "dix": 10, "onze": 11, "douze": 12, "quinze": 15, "vingt": 20,
                "trente": 30, "quarante": 40, "cinquante": 50, "soixante": 60, "cent": 100,
                "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six_": 6, "seven": 7, "eight": 8,
                "nine": 9, "ten": 10, "twelve": 12, "twenty": 20, "thirty": 30}
UNITES = [
    (r"€|euros?|eur", "EUR"), (r"\$|usd|dollars?", "USD"), (r"£|gbp|livres? sterling", "GBP"),
    (r"chf|francs? suisses?", "CHF"),
    (r"%|pour ?cent|pourcents?|percent", "%"),
    (r"jours? ouvr[ée]s|jours? ouvrables|business days?|working days?", "jour ouvré"),
    (r"jours?|days?", "jour"), (r"semaines?|weeks?", "semaine"), (r"mois|months?", "mois"),
    (r"ann[ée]es?|ans|an|years?", "an"), (r"heures?|hours?|h", "heure"), (r"minutes?|min", "minute"),
    (r"m²|m2|m[èe]tres? carr[ée]s|square met(?:er|re)s?", "m²"), (r"km|kilom[èe]tres?", "km"),
    (r"kg|kilos?|kilogrammes?", "kg"), (r"kwh", "kWh"), (r"tonnes?", "t"),
    (r"salari[ée]s?|employ[ée]s?|collaborateurs?|employees", "salarié"), (r"clients?|customers", "client"),
    (r"entreprises?|soci[ée]t[ée]s|companies", "entreprise"), (r"[ée]tapes?|steps?", "étape"),
    (r"points?", "point"), (r"places?", "place"), (r"lots?", "lot"),
]
UNITES_TEMPS = {"jour ouvré", "jour", "semaine", "mois", "an", "heure", "minute"}
_ALT_UNITES = "|".join(u for u, _ in UNITES)
_NB = r"(?:\d{1,3}(?:[ \u00a0\u202f.]\d{3})+|\d+)(?:,\d+|\.\d+)?"
_PERIODES = (r"(?i:mois|ann[ée]e|an|jour|semaine|heure|salari[ée]|utilisateur|personne|poste|"
             r"month|year|day|week|hour|user|employee)\b")
_NB_EN = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"
_MOT_NB = "|".join(sorted((k for k in NOMBRES_MOTS if not k.endswith("_")), key=len, reverse=True))
_VAL = rf"(?:{_NB}|(?i:{_MOT_NB}))"
_MULT = r"(?:k|K|M|Md|(?i:millions?|milliards?|mille|thousand|billion))"
_QTE = re.compile(
    rf"(?<![\w,.])(?P<n1>{_VAL})(?:\s*(?:-|–|à|a|et|to|and)\s*(?P<n2>{_NB}))?\s*(?P<mult>{_MULT})?"
    rf"\s*(?:(?i:d['’]\s*|de\s+|of\s+))?(?P<unite>(?i:{_ALT_UNITES}))(?![\w²])"
    rf"(?P<taxe>\s*(?:HT|TTC|H\.T\.|T\.T\.C\.))?(?P<periode>\s*(?:/\s*|(?i:par|per|a|an)\s+){_PERIODES})?")
_QTE_PREFIXE = re.compile(rf"(?P<unite>[€$£])\s*(?P<n1>{_NB_EN})(?:\s*(?P<mult>k|K|M|bn|million|billion))?"
                          rf"(?P<periode>\s*(?:/\s*|(?i:per|a)\s+){_PERIODES})?")
_DATE_JMA = re.compile(r"(?<!\d)(?P<j>\d{1,2})(?:er)?\s+(?P<m>[A-Za-zéèêûôÉÈÊÛÔ]+)\s+(?P<a>1[89]\d{2}|20\d{2})(?!\d)")
_DATE_NUM = re.compile(r"(?<![\d/])(?P<j>\d{1,2})/(?P<m>\d{1,2})/(?P<a>\d{4})(?![\d/])")
_DATE_ISO = re.compile(r"(?<!\d)(?P<a>\d{4})-(?P<m>\d{2})-(?P<j>\d{2})(?!\d)")
_DATE_MA = re.compile(r"(?<![\w])(?P<m>[A-Za-zéèêûôÉÈÊÛÔ]+)\s+(?P<a>1[89]\d{2}|20\d{2})(?!\d)")
_ANNEE = re.compile(r"(?i:\b(?:en|depuis|d[èe]s|in|since|au|avant|jusqu['’]en|à partir de|fond[ée]e? en|"
                    r"cr[ée]{2}e? en|founded in))\s+(?P<a>1[89]\d{2}|20\d{2})(?!\d)")


def nombre(texte: str, anglais: bool = False) -> float:
    """« 1 200 », « 1.200 », « 1,5 », « trois » ; `anglais` : « 1,500.50 » (virgule des milliers)."""
    t = sans_accents(texte.strip())
    if t in NOMBRES_MOTS:
        return float(NOMBRES_MOTS[t])
    if anglais:
        return float(t.replace(",", ""))
    t = re.sub(r"[ \u00a0\u202f]", "", t)
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", t):
        t = t.replace(".", "")
    return float(t.replace(",", "."))


def unite_canonique(brut: str) -> str:
    b = sans_accents(brut.strip())
    for motif, canon in UNITES:
        if re.fullmatch(sans_accents(motif), b):
            return canon
    return b


def _multiplicateur(m: str | None) -> float:
    if not m:
        return 1.0
    m2 = m.lower()
    if m in ("k", "K") or m2 in ("mille", "thousand"):
        return 1e3
    if m == "M" or m2.startswith("million"):
        return 1e6
    if m == "Md" or m2.startswith("milliard") or m2 in ("billion", "bn"):
        return 1e9
    return 1.0


def _periode(brut: str | None) -> str:
    """« par mois » → « /mois » : 45 € par mois et 45 € par an ne sont pas la même valeur."""
    if not brut:
        return ""
    mot = re.sub(r"^\s*(?:/\s*|(?:par|per|a|an)\s+)", "", brut.strip(), flags=re.I)
    return "/" + unite_canonique(mot)


def _propre(v: float):
    return int(v) if float(v).is_integer() else round(v, 4)


def quantites(phrase: str) -> list[dict]:
    """Les valeurs chiffrées d'une phrase : {texte, min, max, unite, debut, fin}.

    Dates → unité « date » (AAAA-MM-JJ ou AAAA-MM), années introduites par
    « en / depuis / fondé en » → unité « année ». « 1 200 € HT » et
    « 1 200 € TTC » ont des unités différentes : on ne les compare pas.
    """
    trouves: list[dict] = []
    masque = list(phrase)

    def ajouter(m, mini, maxi, unite):
        trouves.append({"texte": m.group(0).strip(), "min": mini, "max": maxi, "unite": unite,
                        "debut": m.start(), "fin": m.end()})
        for i in range(m.start(), m.end()):
            masque[i] = " "

    for m in _DATE_JMA.finditer(phrase):
        mois = MOIS.get(sans_accents(m.group("m")))
        if mois:
            d = f"{m.group('a')}-{mois:02d}-{int(m.group('j')):02d}"
            ajouter(m, d, d, "date")
    for rx in (_DATE_NUM, _DATE_ISO):
        for m in rx.finditer("".join(masque)):
            if 1 <= int(m.group("m")) <= 12 and 1 <= int(m.group("j")) <= 31:
                d = f"{m.group('a')}-{int(m.group('m')):02d}-{int(m.group('j')):02d}"
                ajouter(m, d, d, "date")
    for m in _DATE_MA.finditer("".join(masque)):
        mois = MOIS.get(sans_accents(m.group("m")))
        if mois:
            d = f"{m.group('a')}-{mois:02d}"
            ajouter(m, d, d, "date")
    for m in _ANNEE.finditer("".join(masque)):
        a = int(m.group("a"))
        trouves.append({"texte": m.group("a"), "min": a, "max": a, "unite": "année",
                        "debut": m.start("a"), "fin": m.end("a")})
        for i in range(m.start("a"), m.end("a")):
            masque[i] = " "

    texte = "".join(masque)
    for m in _QTE.finditer(texte):
        unite = unite_canonique(m.group("unite"))
        if sans_accents(m.group("n1")) in ("un", "une", "one") and unite not in UNITES_TEMPS:
            continue  # « une entreprise », « un client » : un article, pas un chiffre
        if unite == "an" and m.group("n2") is None and re.fullmatch(r"1[89]\d{2}|20\d{2}", m.group("n1")):
            continue  # « 2026 ans » n'existe pas : c'est une date mal découpée
        mult = _multiplicateur(m.group("mult"))
        mini = nombre(m.group("n1")) * mult
        maxi = nombre(m.group("n2")) * mult if m.group("n2") else mini
        if m.group("taxe"):
            unite += " " + ("HT" if "H" in m.group("taxe").upper().replace("TTC", "") else "TTC")
        ajouter(m, _propre(mini), _propre(maxi), unite + _periode(m.group("periode")))
    for m in _QTE_PREFIXE.finditer("".join(masque)):
        mult = _multiplicateur(m.group("mult"))
        v = _propre(nombre(m.group("n1"), anglais=True) * mult)
        ajouter(m, v, v, unite_canonique(m.group("unite")) + _periode(m.group("periode")))

    trouves.sort(key=lambda q: q["debut"])
    # « de 1 200 € à 2 000 € » : deux valeurs de même unité reliées par à / et / - forment une fourchette.
    fusion: list[dict] = []
    for q in trouves:
        p = fusion[-1] if fusion else None
        if (p and p["unite"] == q["unite"] and p["unite"] not in ("date", "année")
                and re.fullmatch(r"\s*(?:à|a|et|-|–|to|and)\s*", phrase[p["fin"]:q["debut"]])):
            p.update(max=q["max"], fin=q["fin"], texte=phrase[p["debut"]:q["fin"]].strip())
        else:
            fusion.append(dict(q))
    return fusion


def formater(q: dict | None) -> str:
    if not q:
        return ""

    def f(v):
        if isinstance(v, str):
            return v
        s = f"{v:,.2f}".rstrip("0").rstrip(".") if isinstance(v, float) else f"{v:,}"
        return s.replace(",", "\u202f").replace(".", ",")

    if q["unite"] == "année":
        return str(q["min"])
    val = f(q["min"]) if q["min"] == q["max"] else f"{f(q['min'])}–{f(q['max'])}"
    return f"{val} {q['unite']}".strip()


def meme_valeur(a: dict, b: dict) -> bool:
    return a["unite"] == b["unite"] and a["min"] == b["min"] and a["max"] == b["max"]


# ─── Triplets ─────────────────────────────────────────────────────

# (motif, prédicat canonique, genre). Les formes anglaises ont le prédicat
# français : un site bilingue se compare d'une langue à l'autre.
VERBES = [
    (r"se d[ée]fini(?:t|ssent) comme|d[ée]signe(?:nt)?|signifie(?:nt)?|refers? to|means|stands? for",
     "désigne", "definition"),
    (r"correspond(?:ent)? (?:à|aux?)|corresponds? to", "correspond à", "definition"),
    (r"consiste(?:nt)? (?:à|en)|consists? (?:of|in)", "consiste à", "definition"),
    (r"co[uû]te(?:nt)?|co[uû]tai(?:t|ent)|vaut|valent|s['’][ée]l[èe]ve(?:nt)? à|revien(?:t|nent) à|"
     r"(?:est|sont) factur[ée]e?s?|costs?|is priced at", "coûte", "quantite"),
    (r"dure(?:nt)?|durai(?:t|ent)|lasts?|takes", "dure", "quantite"),
    (r"repr[ée]sente(?:nt)?|atteint|atteignent|represents?|reach(?:es)?", "représente", "quantite"),
    (r"compte(?:nt)?|emploie(?:nt)?|employs", "compte", "quantite"),
    (r"varie(?:nt)? (?:de|entre|selon)|ranges? from|varies", "varie", "quantite"),
    (r"permet(?:tent)? (?:de |d['’]|aux? |à )|allows?|enables?|lets|helps?", "permet de", "relation"),
    (r"propose(?:nt)?|offre(?:nt)?|offers?|provides?", "propose", "relation"),
    (r"comprend|comprennent|inclut|incluent|couvre(?:nt)?|regroupe(?:nt)?|includes?|covers?",
     "comprend", "relation"),
    (r"s['’]applique(?:nt)? (?:à|aux?)|concerne(?:nt)?|applies to|affects", "s'applique à", "relation"),
    (r"s['’]adresse(?:nt)? (?:à|aux?)|(?:est|sont) destin[ée]e?s? (?:à|aux?)|is (?:designed|intended) for",
     "s'adresse à", "relation"),
    (r"accompagne(?:nt)?|assists?|supports?", "accompagne", "relation"),
    (r"classe(?:nt)?|ranks?|classifies", "classe", "relation"),
    (r"calcule(?:nt)?|mesure(?:nt)?|calculates?|measures?", "mesure", "relation"),
    (r"remplace(?:nt)?|replaces?", "remplace", "relation"),
    (r"exige(?:nt)?|impose(?:nt)?|oblige(?:nt)?|requiert|requi[èe]rent|n[ée]cessite(?:nt)?|requires?",
     "exige", "relation"),
    (r"d[ée]pend(?:ent)? (?:de|du|des)|depends on", "dépend de", "relation"),
    (r"(?:a|ont) [ée]t[ée] (?:fond[ée]e?s?|cr[ée]{2}e?s?)(?: en)?|(?:was|were) (?:founded|created)(?: in)?|"
     r"fond[ée]e?s? en|cr[ée]{2}e?s? en", "fondé en", "relation"),
    (r"(?:est|sont) (?:bas[ée]e?s?|situ[ée]e?s?|install[ée]e?s?|implant[ée]e?s?) (?:à|en|au|aux|dans)|"
     r"is (?:based|located|headquartered) in", "est situé à", "relation"),
    (r"intervien(?:t|nent) (?:à|en|au|aux|dans|sur|aupr[èe]s)|operates in", "intervient", "relation"),
    (r"devien(?:t|nent)|becomes?", "devient", "attribut"),
    (r"doi(?:t|vent)|must|(?:has|have) to", "doit", "relation"),
    (r"[ée]tai(?:t|ent)|was|were", "est", "copule"),
    (r"c['’]est|est|sont|is|are", "est", "copule"),
]
# Un sujet n'a qu'une valeur pour ces prédicats : deux objets différents sont une contradiction.
# « propose », « comprend », « accompagne » en admettent plusieurs : on ne les compare pas.
PREDICATS_UNIQUES = {"désigne", "correspond à", "consiste à", "coûte", "dure", "compte", "fondé en",
                     "est situé à", "représente"}
# Élision refusée devant le verbe (« l'aide », « d'offre » sont des noms), sauf « n' » (négation).
_VERBES = [(re.compile(rf"(?<![\w-])(?<![ldjmtsc]['’])(?<!qu['’])(?:{m})(?:\b|(?<=['’\s]))(?!-)", re.I), p, g)
           for m, p, g in VERBES]
# Un sujet ne se termine pas par un mot-outil : « l'optimisation et la [mesure] » est un nom, pas un verbe.
MOTS_OUTILS_FIN = {"le", "la", "les", "l'", "un", "une", "des", "du", "de", "d'", "et", "ou", "a", "en", "au",
                   "aux", "par", "pour", "sur", "the", "a", "an", "of", "and", "or", "to", "que", "qui"}
_NEGATION = re.compile(r"(?i)\s+(?:ne|n['’])\s*$")
_PASSE = re.compile(r"(?i)(?<![\w'’])(?:[ée]tai(?:t|ent)|co[uû]tai(?:t|ent)|durai(?:t|ent)|was|were)\b")
_HISTORIQUE = re.compile(
    r"(?i)\b(?:auparavant|anciennement|historiquement|ancien(?:ne)? (?:bar[èe]me|tarif|r[èe]gle|version)|"
    r"jusqu['’](?:en|au|à)|avant (?:la|le|l['’]|\d)|previously|formerly|until \d{4}|used to)")
_FIN_OBJET = re.compile(r"\s*(?:;|:|\s[—–]\s|\(|,\s*(?:mais|car|donc|alors|tandis|puis|sauf|but|while)\b|"
                        r"\s(?:mais|car|tandis que|alors que|but|whereas)\s)", re.I)
_APPOSITION = re.compile(r"^([^,]{2,60}),\s*([^,]{3,120}),\s*")
_PREPOSITION_TETE = re.compile(r"(?i)^\s*(?:en|depuis|d[èe]s|chez|pour|dans|selon|avec|apr[èe]s|avant|sur|"
                               r"au|aux|à|pendant|lors|in|since|for|with|at|on|after|before|by)\b")
_SIGLE = re.compile(r"\(\s*([A-Z][A-Z0-9&]{1,9})\s*\)")
_CONJ_TETE = re.compile(r"^(?:et|mais|donc|ainsi|enfin|aussi|or|puis|and|but|so)\b[\s,]*", re.I)


def _sujet_valide(s: str) -> bool:
    n = _NEGATION.sub("", " " + norm(s)).strip()
    mots = n.split()
    return bool(jetons(DETERMINANTS.sub("", n))) and len(mots) <= 14 and mots[-1] not in MOTS_OUTILS_FIN \
        and not n.endswith("'")


def _nettoyer_sujet(brut: str) -> tuple[str, str, str | None]:
    """(sujet, contexte, apposition). « En 2026, le taux… » → contexte « En 2026 ».

    « Atlas Conseil, cabinet comptable à Lyon, accompagne… » → sujet
    « Atlas Conseil », apposition « cabinet comptable à Lyon » (une définition implicite).
    """
    s = _CONJ_TETE.sub("", brut.strip())
    contexte, apposition = "", None
    if re.search(r"[:;]", s):
        avant, _, s = s.rpartition(":" if ":" in s else ";")
        contexte, s = avant.strip(), s.strip()
    if s.endswith(","):
        parties = [p.strip() for p in s.rstrip(",").split(",") if p.strip()]
        if len(parties) >= 2 and not _PREPOSITION_TETE.match(parties[0]):
            s, apposition = parties[0], ", ".join(parties[1:])
        else:
            # « Sur un marché saturé, c'est… » : ce qui précède la virgule est un contexte.
            contexte, s = ", ".join(parties), ""
    elif "," in s:
        avant, _, apres = s.rpartition(",")
        enumeration = re.search(r"\s(?:et|ou|and|or)\s", apres) and not _PREPOSITION_TETE.match(s) \
            and len(avant.split()) <= 6
        if _sujet_valide(apres) and not enumeration:
            contexte, s = avant.strip(), apres.strip()
    s = re.sub(r"\s*\([^)]*\)", "", s)
    s = _NEGATION.sub("", " " + s).strip()
    return s.strip(" \"«»“”"), contexte, apposition


def _objet(reste: str) -> str:
    m = _FIN_OBJET.search(reste)
    o = reste[:m.start()] if m else reste
    o = o.strip().rstrip(".!?…").strip(" \"«»“”")
    mots = o.split()
    return " ".join(mots[:25]) + (" …" if len(mots) > 25 else "")


def _premier_verbe(phrase: str, depuis: int = 0):
    """Le verbe du lexique le plus à gauche après `depuis` (le plus long à égalité)."""
    meilleur = None
    for rx, pred, genre in _VERBES:
        for m in rx.finditer(phrase, depuis):
            if meilleur is None or m.start() < meilleur[0].start() or \
                    (m.start() == meilleur[0].start() and m.end() > meilleur[0].end()):
                meilleur = (m, pred, genre)
            break
    return meilleur


def _coordination(reste: str):
    """« … coûte 1 200 € et dure trois semaines » : le « et » suivi d'un verbe du lexique ouvre un second triplet."""
    for c in re.finditer(r",?\s(?:et|puis|and)\s", reste):
        s = _premier_verbe(reste, c.end())
        if s and s[0].start() == c.end():
            return c, s
    return None, None


def _sigles(phrase: str) -> list[dict]:
    """« la déclaration sociale nominative (DSN) » → DSN — désigne — déclaration sociale nominative."""
    res = []
    for m in _SIGLE.finditer(phrase):
        sigle = m.group(1)
        mots = re.findall(r"[\w'’-]+", phrase[:m.start()])[-10:]
        for n in range(1, len(mots) + 1):
            candidats = mots[-n:]
            initiales = "".join(w[0] for w in candidats if sans_accents(w) not in MOTS_VIDES).upper()
            if sans_accents(initiales) == sans_accents(sigle):
                res.append({"sujet": sigle, "predicat": "désigne", "objet": " ".join(candidats),
                            "genre": "definition"})
                break
    return res


def triplets_phrase(phrase: str) -> list[dict]:
    """Les triplets candidats d'une phrase. Heuristique, pas analyse syntaxique :
    le sujet est ce qui précède le premier verbe connu, l'objet ce qui suit
    jusqu'à la fin de la proposition."""
    res: list[dict] = []
    if phrase.rstrip().endswith("?"):
        return res  # une question n'affirme rien ; sa réponse, oui
    historique = bool(_HISTORIQUE.search(phrase) or _PASSE.search(phrase))
    qtes = quantites(phrase)
    trouve = _premier_verbe(phrase)
    app = _APPOSITION.match(phrase)
    if app and not _PREPOSITION_TETE.match(app.group(1)):
        suite = _premier_verbe(phrase, app.end())
        if suite and suite[0].start() == app.end():
            trouve = suite
    # Un « verbe » en tête de sujet (« Le compte pro coûte… ») : on cherche le suivant.
    while trouve:
        avant = phrase[:trouve[0].start()]
        candidat = _nettoyer_sujet(avant)[0]
        if not avant.strip() or not candidat or norm(candidat) in PRONOMS or _sujet_valide(candidat):
            break
        trouve = _premier_verbe(phrase, trouve[0].end())
    if trouve:
        m, pred, genre = trouve
        negation = bool(_NEGATION.search(" " + phrase[:m.start()].rstrip()))
        sujet, contexte, apposition = _nettoyer_sujet(phrase[:m.start()])
        implicite = not sujet or _est_pronom(sujet) or bool(_PREPOSITION_TETE.match(sujet))
        if apposition and not implicite:
            res.append({"sujet": sujet, "predicat": "est", "objet": apposition, "genre": "definition",
                        "valeur": next((q for q in qtes if q["texte"] in apposition), None)})
        debut = m.end()
        while True:
            reste = phrase[debut:]
            coord, suivant = _coordination(reste)
            fin = coord.start() if coord else len(reste)
            objet = _objet(reste[:fin])
            if genre == "copule" and re.match(r"(?i)(?:de|d['’]|of)\s", objet) and \
                    any(debut <= q["debut"] < debut + fin for q in qtes):
                objet = re.sub(r"(?i)^(?:de|d['’]|of)\s*", "", objet)
            if genre == "copule" and re.match(r"(?i)(?:un|une|le|la|l['’]|les|a|an|the)\b", objet):
                genre = "definition"
            valeur = next((q for q in qtes if debut <= q["debut"] < debut + fin), None)
            if negation:
                objet = re.sub(r"(?i)^(?:pas|plus|jamais)\b\s*", "", objet)
            # « Mieux vaut… », « Combien coûte… » : un prédicat de quantité sans quantité n'affirme rien.
            if objet and not (genre == "quantite" and valeur is None):
                neg = (f"n'{pred} pas" if sans_accents(pred)[0] in "aeiouy" else f"ne {pred} pas")
                res.append({"sujet": sujet, "predicat": neg if negation else pred,
                            "objet": objet, "genre": genre,
                            "valeur": valeur, "sujet_implicite": implicite, "historique": historique,
                            "contexte": contexte})
            if not coord:
                break
            m, pred, genre = suivant
            debut = debut + m.end()
            negation = False
    for t in _sigles(phrase):
        res.append({**t, "valeur": None, "sujet_implicite": False, "historique": historique, "contexte": ""})
    # Chiffres qu'aucun triplet ne porte : relevés quand même, sujet deviné (confiance faible).
    portes = {id(t.get("valeur")) for t in res if t.get("valeur")}
    for q in qtes:
        if id(q) in portes:
            continue
        avant = re.sub(r"[,;:]$", "", phrase[:q["debut"]].strip())
        sujet = " ".join(avant.split()[-6:]) if avant else ""
        res.append({"sujet": sujet, "predicat": "(chiffre)", "objet": q["texte"], "genre": "chiffre",
                    "valeur": q, "sujet_implicite": not _sujet_valide(sujet), "historique": historique,
                    "contexte": ""})
    for t in res:
        t.setdefault("valeur", None)
        t.setdefault("sujet_implicite", False)
        t.setdefault("historique", historique)
        t.setdefault("contexte", "")
        t["phrase"] = phrase
    return res


def predicat_canonique(p: str) -> str:
    """« sont situés à », « is based in » → « est situé à » ; un prédicat hors lexique reste tel quel."""
    m = _premier_verbe(p or "")
    if m and m[0].start() == 0 and m[0].end() >= len((p or "").strip()) - 1:
        return m[1]
    return norm(p)


PREDICATS_CANONIQUES = {c for _, c, _ in VERBES}


def valeurs_affirmees(phrase: str, predicat: str) -> list[dict]:
    """Les valeurs que la phrase attache à ce prédicat. Hors lexique : toutes ses valeurs chiffrées.

    « Le bilan annuel coûte 1 200 € HT, acompte de 400 € HT à la commande » :
    pour « coûte », seule 1 200 € HT compte — l'acompte n'est pas une contradiction."""
    if predicat not in PREDICATS_CANONIQUES:
        return quantites(phrase)
    return [t["valeur"] for t in triplets_phrase(phrase)
            if t["predicat"] == predicat and t.get("valeur") and not t["historique"]]


def _est_pronom(s: str) -> bool:
    """« Il », « cela », « ce dernier », « cette offre » : le lecteur doit remonter pour savoir de quoi on parle."""
    n = norm(s)
    mots = n.split()
    return n in PRONOMS or n.startswith("c'") or \
        (bool(mots) and mots[0] in PRONOMS | DEMONSTRATIFS and len(mots) <= 2)


# ─── Lecture des pages ────────────────────────────────────────────

IGNORES = {"script", "style", "noscript", "svg", "template", "iframe", "head", "button", "select"}
HORS = {"nav", "footer", "aside", "form", "dialog"}
BLOCS = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th", "blockquote", "dd", "dt", "figcaption",
         "summary", "caption", "div", "section", "article", "main", "header", "tr", "ul", "ol", "table"}
VIDES = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source",
         "track", "wbr"}


class _Lecteur(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.pile: list[tuple[str, bool, bool]] = []  # (balise, hors zone, dans main)
        self.blocs: list[dict] = []
        self.tampon: list[str] = []
        self.titre, self._dans_titre = "", False
        self.ignore = 0

    def _vider(self) -> None:
        texte = re.sub(r"\s+", " ", "".join(self.tampon)).strip()
        self.tampon = []
        if texte:
            genre = next((t for t, _, _ in reversed(self.pile) if re.fullmatch(r"h[1-6]|li|td|th|p", t)), "texte")
            self.blocs.append({"genre": genre, "texte": texte,
                               "hors": any(h for _, h, _ in self.pile),
                               "main": any(m for _, _, m in self.pile)})

    def handle_starttag(self, tag, attrs):
        if tag in VIDES:
            if tag == "br":
                self.tampon.append(" ")
            return
        a = {k: (v or "") for k, v in attrs}
        if tag == "title":
            self._dans_titre = True
        if tag in IGNORES:
            self.ignore += 1
        if tag in BLOCS or tag in HORS:
            self._vider()
        hors = tag in HORS or a.get("role") in ("navigation", "contentinfo", "complementary") or \
            bool(re.search(r"(?:^|[\s_-])(?:nav|menu|sidebar|cookies?|breadcrumbs?|footer|share)(?:$|[\s_-])",
                           a.get("class", "") + " " + a.get("id", ""), re.I)) and tag not in ("body", "main", "article")
        self.pile.append((tag, hors, tag in ("main", "article") or a.get("role") == "main"))

    def handle_endtag(self, tag):
        if tag in VIDES:
            return
        if tag == "title":
            self._dans_titre = False
        if tag in IGNORES and self.ignore:
            self.ignore -= 1
        idx = next((i for i in range(len(self.pile) - 1, -1, -1) if self.pile[i][0] == tag), None)
        if idx is None:
            return
        if tag in BLOCS or tag in HORS:
            self._vider()
        del self.pile[idx:]

    def handle_data(self, data):
        if self._dans_titre:
            self.titre += data
            return
        if not self.ignore:
            self.tampon.append(data)


def _page(blocs: list[dict], titre: str = "", jsonld: list | None = None, source: str = "") -> dict:
    """Assemble la page : blocs retenus, h1, titres, phrases numérotées par position en mots."""
    h1 = next((b["texte"] for b in blocs if b["genre"] == "h1"), "")
    titres = [b["texte"] for b in blocs if re.fullmatch(r"h[2-6]", b["genre"])]
    phrases, position = [], 0
    for b in blocs:
        if re.fullmatch(r"h[1-6]", b["genre"]):
            position += len(b["texte"].split())
            continue
        for p in decouper_phrases(b["texte"]):
            phrases.append({"phrase": p, "position": position, "norm": norm(p)})
            position += len(p.split())
    texte = "\n".join(b["texte"] for b in blocs)
    return {"source": source, "titre": re.sub(r"\s+", " ", titre).strip(), "h1": h1, "titres": titres,
            "texte": texte, "texte_norm": norm(texte), "phrases": phrases, "mots": position,
            "jsonld": jsonld or []}


def lire_html(html: str, source: str = "") -> dict:
    """Contenu principal : <main>/<article> s'ils portent au moins 50 mots, sinon la page
    moins navigation, pied de page et barres latérales. Le JSON-LD est lu à part."""
    lecteur = _Lecteur()
    try:
        lecteur.feed(html or "")
        lecteur.close()
    except Exception:  # noqa: BLE001 — une page mal formée se lit en partie, elle ne plante pas
        pass
    lecteur._vider()
    blocs = [b for b in lecteur.blocs if not b["hors"]]
    if sum(len(b["texte"].split()) for b in blocs if b["main"]) >= 50:
        blocs = [b for b in blocs if b["main"]]
    return _page(blocs, lecteur.titre, analyser_html(html or "")["blocs"], source)


def lire_markdown(md: str, source: str = "") -> dict:
    md = re.sub(r"\A---\n.*?\n---\n", "", md or "", flags=re.S)  # front matter
    blocs, para = [], []

    def fermer():
        if para:
            blocs.append({"genre": "p", "texte": " ".join(para)})
            para.clear()

    for ligne in md.splitlines():
        s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", ligne.strip())
        s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
        s = re.sub(r"[*_`]{1,3}", "", s)
        h = re.match(r"(#{1,6})\s+(.*?)\s*#*$", s)
        li = re.match(r"(?:[-*+]|\d+[.)])\s+(.*)", s)
        if not s:
            fermer()
        elif h:
            fermer()
            blocs.append({"genre": f"h{len(h.group(1))}", "texte": h.group(2)})
        elif li:
            fermer()
            blocs.append({"genre": "li", "texte": li.group(1)})
        elif s.startswith("|"):
            fermer()
            if not re.fullmatch(r"[|\s:-]+", s):
                blocs.append({"genre": "td", "texte": ". ".join(c.strip() for c in s.strip("|").split("|")
                                                                  if c.strip())})
        else:
            para.append(s.lstrip("> "))
    fermer()
    titre = next((b["texte"] for b in blocs if b["genre"] == "h1"), "")
    return _page(blocs, titre, [], source)


CLES_NON_TEXTE = {"url", "href", "src", "image", "slug", "id", "@id", "@type", "@context", "icon", "lien",
                  "canonical", "template", "layout", "class", "type", "lang", "date", "datePublished",
                  "dateModified", "sameAs", "logo"}


def lire_json(brut: str, source: str = "") -> dict:
    """Un fichier de contenu JSON : chaque chaîne est un bloc de texte. Un JSON-LD est lu comme tel."""
    try:
        objet = json.loads(brut)
    except ValueError:
        return _page([], "", [], source)
    if isinstance(objet, dict) and ("@context" in objet or "@graph" in objet):
        return _page([], "", [objet], source)
    blocs: list[dict] = []

    def parcourir_json(o, cle=""):
        if isinstance(o, dict):
            for k, v in o.items():
                parcourir_json(v, k)
        elif isinstance(o, list):
            for v in o:
                parcourir_json(v, cle)
        elif isinstance(o, str) and cle not in CLES_NON_TEXTE and len(o.split()) >= 3:
            texte = re.sub(r"<[^>]+>", " ", o)
            genre = "h2" if cle.lower() in ("title", "titre", "h1", "h2", "heading", "question") else "p"
            if cle.lower() in ("h1",):
                genre = "h1"
            blocs.append({"genre": genre, "texte": re.sub(r"\s+", " ", texte).strip()})

    parcourir_json(objet)
    return _page(blocs, "", [], source)


def lire_fichier(chemin: Path) -> dict:
    brut = chemin.read_text(encoding="utf-8", errors="replace")
    ext = chemin.suffix.lower()
    if ext in (".html", ".htm") or brut.lstrip().startswith("<"):
        return lire_html(brut, str(chemin))
    if ext == ".json":
        return lire_json(brut, str(chemin))
    return lire_markdown(brut, str(chemin))


def telecharger(url: str) -> str:
    """HTML initial d'une URL publique, par l'aide commune du dépôt (adresses internes refusées)."""
    try:
        from _contenu import PageIllisible, telecharger as _telecharger
    except ImportError:
        raise SystemExit("✗ lecture d'URL indisponible (scripts/_contenu.py absent) : "
                         "enregistrez la page en .html et passez le fichier")
    try:
        return _telecharger(url)[0]
    except PageIllisible as exc:
        raise SystemExit(f"✗ {url} illisible : {exc}")


def lire_source(source: str | None, texte: str | None = None) -> dict:
    if texte is not None:
        return lire_markdown(texte, "texte")
    if re.match(r"https?://", source or ""):
        return lire_html(telecharger(source), source)
    chemin = Path(source or "")
    if not chemin.is_file():
        raise SystemExit(f"✗ fichier introuvable : {source}")
    return lire_fichier(chemin)


# ─── Entités du JSON-LD ───────────────────────────────────────────

ROLES = ("about", "mentions", "knowsAbout", "category", "areaServed", "author", "provider", "publisher",
         "founder", "subjectOf")
# Nœuds de structure : leur nom est un titre de page, pas une entité.
TYPES_STRUCTURE = {"WebPage", "WebSite", "CollectionPage", "AboutPage", "ContactPage", "ProfilePage", "FAQPage",
                   "ItemPage", "BreadcrumbList", "ListItem", "ItemList", "Question", "Answer", "ImageObject",
                   "SearchAction", "EntryPoint", "BlogPosting", "Article", "NewsArticle", "DefinedTermSet"}
_QID = re.compile(r"wikidata\.org/(?:wiki|entity)/(Q\d+)", re.I)


def qid_de(valeurs) -> str | None:
    for s in liste(valeurs):
        m = _QID.search(s) if isinstance(s, str) else None
        if m:
            return m.group(1).upper()
    return None


def entites_jsonld(blocs: list) -> list[dict]:
    """Les entités déclarées : {role, nom, type, sameAs, qid, id}. Références @id résolues dans le graphe."""
    noeuds = [n for b in blocs for n, _ in parcourir(b)]
    index = {n["@id"]: n for n in noeuds if isinstance(n.get("@id"), str)}
    res, vus, objets = [], set(), set()

    def ajouter(role, e):
        if isinstance(e, dict) and set(e) == {"@id"}:
            e = index.get(e["@id"], e)
        if isinstance(e, dict):
            if role == "noeud" and id(e) in objets:
                return  # déjà relevé comme about/mentions/provider…
            objets.add(id(e))
        if isinstance(e, str):
            e = {"name": e}
        if not isinstance(e, dict):
            return
        nom = e.get("name") or e.get("headline") or ""
        nom = nom if isinstance(nom, str) else str(nom)
        cle = (role, norm(nom), e.get("@id"))
        if cle in vus or not (nom or e.get("@id")):
            return
        vus.add(cle)
        same = [s for s in liste(e.get("sameAs")) if isinstance(s, str)]
        res.append({"role": role, "nom": nom, "type": ", ".join(types_de(e)) or "Thing", "sameAs": same,
                    "qid": qid_de(same), "id": e.get("@id")})

    for n in noeuds:
        for role in ROLES:
            for v in liste(n.get(role)):
                ajouter(role, v)
        if "DefinedTerm" in types_de(n):
            ajouter("DefinedTerm", n)
        elif n.get("name") and not set(types_de(n)) & TYPES_STRUCTURE:
            ajouter("noeud", n)
    return res


# ─── Le registre du projet ────────────────────────────────────────

def lire_csv(chemin: Path) -> list[dict]:
    """CSV avec en-tête ; les lignes qui commencent par # sont des commentaires (exemples du gabarit)."""
    if not chemin or not Path(chemin).is_file():
        return []
    texte = Path(chemin).read_text(encoding="utf-8-sig")
    lignes = [l for l in texte.splitlines(keepends=True) if l.strip() and not l.lstrip().startswith("#")]
    return [{(k or "").strip(): (v or "").strip() for k, v in r.items()}
            for r in csv.DictReader(io.StringIO("".join(lignes)))]


def _plusieurs(v: str) -> list[str]:
    return [x.strip() for x in re.split(r"\s*\|\s*|\s+(?=https?://)", v or "") if x.strip()]


def normaliser_qid(v: str) -> str:
    m = re.search(r"(Q\d+)", v or "", re.I)
    return m.group(1).upper() if m else ""


def charger_entites(chemin) -> list[dict]:
    """`memoire/entites.csv` (entite, type, qid, sameAs, definition[, alias]).

    Accepte aussi l'ancien registre JSON (`memoire/entites.json`)."""
    if not chemin or not Path(chemin).is_file():
        return []
    chemin = Path(chemin)
    if chemin.suffix.lower() == ".json":
        brut = json.loads(chemin.read_text(encoding="utf-8"))
        lignes = [{"entite": v.get("name") or k, "type": v.get("type") or "Thing",
                   "qid": v.get("wikidata") or "", "sameAs": " | ".join(x for x in (v.get("wikipedia"),) if x),
                   "definition": v.get("definition") or v.get("description_wikidata") or "",
                   "alias": " | ".join(v.get("alias") or [])} for k, v in brut.items()]
    else:
        lignes = lire_csv(chemin)
    res = []
    for l in lignes:
        if not l.get("entite"):
            continue
        res.append({"entite": l["entite"], "type": l.get("type") or "Thing", "qid": normaliser_qid(l.get("qid", "")),
                    "sameAs": _plusieurs(l.get("sameAs", "")), "definition": l.get("definition", ""),
                    "alias": _plusieurs(l.get("alias", ""))})
    return res


def charger_triplets(chemin) -> list[dict]:
    """`memoire/triplets.csv` (sujet, predicat, objet, source, date_verif, pages)."""
    res = []
    for l in lire_csv(Path(chemin)) if chemin else []:
        if l.get("sujet") and l.get("objet"):
            res.append({**l, "pages": _plusieurs(l.get("pages", "")) or ["*"]})
    return res


def id_page(source: str) -> str:
    """« https://x.fr/offres/bilan-annuel/ » et « contenus/bilan-annuel.html » → « bilan-annuel »."""
    s = re.sub(r"^https?://[^/]+", "", (source or "").strip()).split("?")[0].split("#")[0].strip("/")
    dernier = s.rsplit("/", 1)[-1]
    dernier = re.sub(r"\.(?:html?|md|markdown|json|txt)$", "", dernier, flags=re.I)
    return "" if dernier in ("index", "accueil", "home") else sans_accents(dernier)


def concerne(triplet: dict, page: str) -> bool:
    cible = id_page(page)
    return any(p == "*" or id_page(p) == cible for p in triplet["pages"])


def formes(entite: dict) -> list[str]:
    return [entite["entite"], *entite.get("alias", [])]


def entite_du_sujet(sujet: str, entites: list[dict]) -> dict | None:
    c = cle_sujet(sujet)
    return next((e for e in entites if any(cle_sujet(f) == c for f in formes(e))), None)


def url_wikidata(qid: str) -> str:
    return f"https://www.wikidata.org/wiki/{qid}"


# ─── extraire ─────────────────────────────────────────────────────

def extraire(page: dict, tete: int = TETE_MOTS) -> dict:
    triplets = []
    implicites, chargees = [], []
    for p in page["phrases"]:
        ts = triplets_phrase(p["phrase"])
        for t in ts:
            t["position"] = p["position"]
            t["en_tete"] = p["position"] < tete
        triplets += ts
        faits = [t for t in ts if t["genre"] != "chiffre" or t.get("valeur")]
        vrais = [t for t in ts if t["genre"] != "chiffre"]
        if p["position"] < tete and vrais and all(t["sujet_implicite"] for t in vrais):
            implicites.append(p["phrase"])
        unites = {t["valeur"]["unite"] for t in faits if t.get("valeur")}
        if len({(t["predicat"], cle_sujet(t["sujet"])) for t in faits if t["genre"] != "chiffre"}) >= 3 \
                or len(unites) >= 3:
            chargees.append(p["phrase"])
    for t in triplets:
        t["valeur_texte"] = formater(t.get("valeur"))
    entites = entites_jsonld(page["jsonld"])
    return {"source": page["source"], "titre": page["titre"], "h1": page["h1"], "mots": page["mots"],
            "triplets": triplets, "entites_jsonld": entites,
            "sujets_implicites_en_tete": implicites, "phrases_chargees": chargees}


# ─── verifier ─────────────────────────────────────────────────────

def _sujet_dans(phrase_norm: str, sujet: str, entites: list[dict]) -> bool:
    e = entite_du_sujet(sujet, entites)
    variantes = formes(e) if e else [sujet]
    for v in variantes:
        c = cle_sujet(v)
        if c and contient(phrase_norm, c):
            return True
    rs = radicaux(sujet)
    return bool(rs) and len(rs & radicaux(phrase_norm)) / len(rs) >= 0.75


def statut_triplet(req: dict, page: dict, entites: list[dict], tete: int = TETE_MOTS) -> dict:
    """affirmé · implicite (valeur présente, sujet remplacé par un pronom) · contredit · absent."""
    q_ref = quantites(req["objet"])
    r_obj = radicaux(req["objet"])
    pred_ref = predicat_canonique(req["predicat"])
    res = {"sujet": req["sujet"], "predicat": req["predicat"], "objet": req["objet"], "statut": "absent",
           "phrase": "", "position": None, "en_tete": False, "trouve": ""}
    phrases = page["phrases"]
    candidat_contredit = None
    for i, p in enumerate(phrases):
        a_sujet = _sujet_dans(p["norm"], req["sujet"], entites)
        autre = ""
        if q_ref:
            qs = quantites(p["phrase"])
            ok = all(any(meme_valeur(r, q) for q in qs) for r in q_ref)
            if a_sujet and not ok:
                autre = next((formater(q) for q in valeurs_affirmees(p["phrase"], pred_ref) for r in q_ref
                              if q["unite"] == r["unite"] and not meme_valeur(r, q)), "")
        else:
            ok = bool(r_obj) and len(r_obj & radicaux(p["phrase"])) / len(r_obj) >= 0.6
            if a_sujet and not ok and pred_ref in PREDICATS_UNIQUES:
                # « Atlas Conseil est situé à Villeurbanne » face à « … Lyon » au registre.
                autre = next((t["objet"] for t in triplets_phrase(p["phrase"])
                              if t["predicat"] == pred_ref and not t["sujet_implicite"]
                              and _sujet_dans(norm(t["sujet"]), req["sujet"], entites)), "")
        if a_sujet and ok:
            res.update(statut="affirmé", phrase=p["phrase"], position=p["position"], en_tete=p["position"] < tete)
            return res
        if ok and res["statut"] == "absent" and i and _sujet_dans(phrases[i - 1]["norm"], req["sujet"], entites):
            res.update(statut="implicite", phrase=p["phrase"], position=p["position"])
        if a_sujet and autre and not _HISTORIQUE.search(p["phrase"]) and candidat_contredit is None:
            candidat_contredit = (p, autre)
    if candidat_contredit and res["statut"] == "absent":
        p, autre = candidat_contredit
        res.update(statut="contredit", phrase=p["phrase"], position=p["position"], trouve=autre)
    return res


def saillance(page: dict, noms: dict[str, list[str]]) -> list[dict]:
    """Score de saillance heuristique : H1 3, title 2, 100 premiers mots 2, un H2-H6 1, + occurrences (plafond 5).

    Approximation de ce que mesure un modèle d'entités : est-ce bien de ça
    que parle la page, ou est-ce un mot parmi d'autres ?"""
    intro = norm(" ".join(p["phrase"] for p in page["phrases"] if p["position"] < 100))
    h1, titre = norm(page["h1"]), norm(page["titre"])
    titres = [norm(t) for t in page["titres"]]
    res = []
    for nom, variantes in noms.items():
        occ = sum(contient(page["texte_norm"], v) for v in variantes)
        score = (3 * any(contient(h1, v) for v in variantes) + 2 * any(contient(titre, v) for v in variantes)
                 + 2 * any(contient(intro, v) for v in variantes)
                 + 1 * any(contient(t, v) for t in titres for v in variantes) + min(occ, 10) / 2)
        res.append({"entite": nom, "occurrences": occ, "score": round(score, 1)})
    res.sort(key=lambda x: -x["score"])
    haut = res[0]["score"] if res and res[0]["score"] else 1
    for i, r in enumerate(res, 1):
        r["rang"], r["relative"] = i, round(r["score"] / haut, 2)
    return res


def verifier(page: dict, entites: list[dict], triplets: list[dict], page_id: str, tous: bool = False,
             tete: int = TETE_MOTS) -> dict:
    requis = [t for t in triplets if tous or concerne(t, page_id)]
    statuts = [statut_triplet(t, page, entites, tete) for t in requis]
    decl = entites_jsonld(page["jsonld"])
    declarees = [d for d in decl if d["role"] in ("about", "mentions", "DefinedTerm", "knowsAbout", "category",
                                                   "areaServed", "noeud", "provider", "author")]
    constats: list[dict] = []

    def dit(gravite, entite, message):
        constats.append({"gravite": gravite, "entite": entite, "message": message})

    visibles = []
    for e in entites:
        occ = sum(contient(page["texte_norm"], f) for f in formes(e))
        if not occ:
            continue
        visibles.append(e)
        cibles = {norm(f) for f in formes(e)}
        trouvees = [d for d in declarees if (e["qid"] and d["qid"] == e["qid"]) or norm(d["nom"]) in cibles]
        if not trouvees:
            dit("attention", e["entite"], f"nommée {occ} fois dans le texte, absente du JSON-LD (about/mentions)")
            continue
        for d in trouvees:
            if e["qid"] and d["qid"] and d["qid"] != e["qid"]:
                dit("erreur", e["entite"], f"{d['role']} : QID {d['qid']} ≠ registre {e['qid']} — sameAs faux")
            elif e["qid"] and not d["qid"]:
                dit("attention", e["entite"], f"{d['role']} sans sameAs Wikidata ({url_wikidata(e['qid'])})")
        if not e["qid"] and not e["sameAs"]:
            dit("info", e["entite"], "aucun QID ni sameAs au registre : chercher avec `triplets.py wikidata`")
    noms_registre = {norm(f) for e in entites for f in formes(e)}
    qids_registre = {e["qid"] for e in entites if e["qid"]}
    for d in declarees:
        if d["role"] not in ("about", "mentions"):
            continue
        if d["nom"] and not contient(page["texte_norm"], d["nom"]) and \
                not any(contient(page["texte_norm"], f) for e in entites if d["qid"] and e["qid"] == d["qid"]
                        for f in formes(e)):
            dit("attention", d["nom"], f"{d['role']} : entité invisible dans le contenu principal")
        if norm(d["nom"]) not in noms_registre and d["qid"] not in qids_registre:
            dit("info", d["nom"], f"{d['role']} hors registre" + (" et sans sameAs" if not d["sameAs"] else
                                                                  " : sameAs non vérifié")
                + " — à inscrire dans memoire/entites.csv")

    noms = {e["entite"]: formes(e) for e in visibles}
    for d in declarees:
        if d["role"] in ("about", "mentions") and d["nom"] and d["nom"] not in noms:
            noms[d["nom"]] = [d["nom"]]
    sal = saillance(page, noms)
    rang = {s["entite"]: s for s in sal}
    abouts = [d["nom"] for d in declarees if d["role"] == "about" and d["nom"]]
    for nom in abouts:
        cle = next((k for k in rang if norm(k) == norm(nom)
                    or any(norm(f) == norm(nom) for e in entites if e["entite"] == k for f in formes(e))), None)
        s = rang.get(cle) if cle else None
        if s and s["rang"] > 3 and s["relative"] < 0.5:
            dit("attention", nom, f"about peu saillant (rang {s['rang']}, {s['relative']:.0%} du plus saillant) : "
                                  "le nommer dans le H1, le title ou l'introduction")
    if sal and sal[0]["score"] and abouts and not any(norm(sal[0]["entite"]) == norm(a) for a in abouts):
        dit("info", sal[0]["entite"], "entité la plus saillante de la page, absente de about")

    affirmes = sum(1 for s in statuts if s["statut"] == "affirmé")
    ent_ok = sum(1 for e in visibles if not any(c["entite"] == e["entite"] and c["gravite"] != "info"
                                                  for c in constats))
    return {
        "page": page_id or page["source"], "source": page["source"],
        "triplets": statuts,
        "couverture_triplets": round(100 * affirmes / len(statuts)) if statuts else None,
        "en_tete": sum(1 for s in statuts if s["en_tete"]),
        "contredits": sum(1 for s in statuts if s["statut"] == "contredit"),
        "entites_visibles": len(visibles),
        "couverture_entites": round(100 * ent_ok / len(visibles)) if visibles else None,
        "saillance": sal[:10], "constats": constats,
    }


# ─── coherence ────────────────────────────────────────────────────

def pages_de(cibles: list[str]) -> list[dict]:
    pages = []
    for c in cibles:
        p = Path(c)
        if p.is_dir():
            fichiers = sorted(f for f in p.rglob("*") if f.is_file() and f.suffix.lower() in EXTENSIONS
                              and not any(x.startswith(".") or x == "node_modules" for x in f.parts))
            pages += [lire_fichier(f) for f in fichiers]
        elif p.is_file():
            pages.append(lire_fichier(p))
        elif re.match(r"https?://", c):
            pages.append(lire_source(c))
        else:
            print(f"  ! ignoré (introuvable) : {c}", file=sys.stderr)
    return pages


def urls_de(fichier: str, maxi: int) -> list[str]:
    """Une URL par ligne, ou un CSV avec une colonne url (export de crawl_site.py : statut 200 seulement)."""
    texte = Path(fichier).read_text(encoding="utf-8-sig")
    premiere = texte.splitlines()[0] if texte.strip() else ""
    if "," in premiere and "url" in premiere.lower():
        urls = [l.get("url", "") for l in csv.DictReader(io.StringIO(texte))
                if str(l.get("statut", "200")).strip() in ("200", "")]
    else:
        urls = [l.strip() for l in texte.splitlines()]
    return [u for u in urls if re.match(r"https?://", u)][:maxi]


def coherence(pages: list[dict], entites: list[dict] | None = None, registre: list[dict] | None = None,
              textes: bool = False) -> dict:
    """Un même sujet + prédicat, deux valeurs : c'est la contradiction que les moteurs IA reprennent."""
    entites, registre = entites or [], registre or []
    groupes: dict[tuple, list] = defaultdict(list)
    for page in pages:
        for t in extraire(page)["triplets"]:
            if t["sujet_implicite"] or t["historique"] or t["genre"] == "chiffre":
                continue
            e = entite_du_sujet(t["sujet"], entites)
            cle = cle_sujet(e["entite"]) if e else cle_sujet(t["sujet"])
            if not cle or cle in SUJETS_VAGUES:
                continue
            groupes[(cle, t["predicat"])].append({**t, "page": page["source"],
                                                  "sujet_affiche": e["entite"] if e else t["sujet"]})

    lignes = []
    for (cle, pred), ts in sorted(groupes.items()):
        par_unite = defaultdict(lambda: defaultdict(set))
        for t in ts:
            if t.get("valeur"):
                par_unite[t["valeur"]["unite"]][formater(t["valeur"])].add(t["page"])
        for unite, valeurs in par_unite.items():
            if len(valeurs) > 1:
                lignes.append({"nature": "contradiction chiffrée", "sujet": ts[0]["sujet_affiche"], "predicat": pred,
                               "valeurs": {v: sorted(p) for v, p in valeurs.items()}})
        if textes and pred in PREDICATS_UNIQUES:
            objets = defaultdict(set)
            for t in ts:
                if not t.get("valeur") and t["genre"] in ("definition", "copule", "attribut"):
                    objets[norm(t["objet"])].add(t["page"])
            distincts = list(objets)
            if len(distincts) > 1:
                r = [radicaux(o) for o in distincts]
                proches = all(len(a & b) / max(1, len(a | b)) >= 0.5 for i, a in enumerate(r) for b in r[i + 1:])
                if not proches:
                    lignes.append({"nature": "formulations divergentes", "sujet": ts[0]["sujet_affiche"],
                                   "predicat": pred, "valeurs": {o: sorted(p) for o, p in objets.items()}})

    # Écart au registre : le sujet, le prédicat et une valeur de même unité, mais pas la valeur de référence.
    for ref in registre:
        q_ref = quantites(ref["objet"])
        pred = predicat_canonique(ref["predicat"])
        if not q_ref:
            if pred not in PREDICATS_UNIQUES:
                continue
            e = entite_du_sujet(ref["sujet"], entites)
            r_ref = radicaux(ref["objet"])
            ecarts = defaultdict(set)
            for t in groupes.get((cle_sujet(e["entite"]) if e else cle_sujet(ref["sujet"]), pred), []):
                r = radicaux(t["objet"])
                if r_ref and not r_ref <= r and len(r_ref & r) / len(r_ref | r) < 0.5:
                    ecarts[t["objet"]].add(t["page"])
            if ecarts:
                valeurs = {f"{ref['objet']} (registre)": [ref.get("source") or "memoire/triplets.csv"]}
                valeurs.update({v: sorted(p) for v, p in ecarts.items()})
                lignes.append({"nature": "écart au registre", "sujet": ref["sujet"], "predicat": ref["predicat"],
                               "valeurs": valeurs})
            continue
        ecarts = defaultdict(set)
        for page in pages:
            for p in page["phrases"]:
                if _HISTORIQUE.search(p["phrase"]) or not _sujet_dans(p["norm"], ref["sujet"], entites):
                    continue
                qs = valeurs_affirmees(p["phrase"], pred)
                for r in q_ref:
                    if any(meme_valeur(r, q) for q in qs):
                        continue
                    for q in qs:
                        if q["unite"] == r["unite"]:
                            ecarts[formater(q)].add(page["source"])
        if ecarts:
            valeurs = {f"{formater(q_ref[0])} (registre)": [ref.get("source") or "memoire/triplets.csv"]}
            valeurs.update({v: sorted(p) for v, p in ecarts.items()})
            lignes.append({"nature": "écart au registre", "sujet": ref["sujet"], "predicat": ref["predicat"],
                           "valeurs": valeurs})
    return {"pages": len(pages), "lignes": lignes,
            "contradictions": sum(1 for l in lignes if l["nature"] != "formulations divergentes")}


# ─── jsonld ───────────────────────────────────────────────────────

# Types qu'un nœud recopié en about/mentions ne doit pas porter : une seconde Organization
# ou un Product sur la page crée un doublon que Google ignore, un logiciel cité en
# SoftwareApplication déclenche les exigences du rich result. Ils partent en Thing + sameAs.
TYPES_EN_THING = {"Organization", "Corporation", "LocalBusiness", "ProfessionalService", "Product",
                  "SoftwareApplication", "WebApplication", "MobileApplication", "WebSite", "Article",
                  "BlogPosting", "NewsArticle"}


def noeud_entite(e: dict, glossaire: str | None = None) -> dict:
    """Le nœud d'une entité du registre. Un sameAs qui porte un # (« https://site/#organization »)
    est l'@id d'un nœud du graphe : on pose une référence, pas une copie."""
    ref = next((s for s in e.get("sameAs", []) if "#" in s), None)
    if ref:
        return {"@id": ref}
    t = e.get("type") or "Thing"
    n = {"@type": "Thing" if t in TYPES_EN_THING else t, "name": e["entite"]}
    if n["@type"] == "DefinedTerm":
        if e.get("definition"):
            n["description"] = e["definition"]
        if glossaire:
            n["inDefinedTermSet"] = {"@id": glossaire}
    same = ([url_wikidata(e["qid"])] if e.get("qid") else []) + \
        [s for s in e.get("sameAs", []) if s.startswith("https://")]
    same = list(dict.fromkeys(same))
    if same:
        n["sameAs"] = same
    return n


def trouver(nom: str, entites: list[dict]) -> dict | None:
    n = norm(nom)
    return next((e for e in entites if any(norm(f) == n for f in formes(e)) or e["qid"] == nom.upper()), None)


def fragment_jsonld(entites: list[dict], about: list[str], mentions: list[str], url: str | None = None,
                    glossaire: str | None = None) -> tuple[dict, list[str]]:
    avis: list[str] = []

    def noeuds(noms, role, maxi):
        res, vus = [], set()
        for nom in noms:
            e = trouver(nom, entites)
            if e is None:
                avis.append(f"{role} « {nom} » hors registre : posé sans sameAs (vérifier avant d'ajouter un QID)")
                e = {"entite": nom, "type": "Thing", "qid": "", "sameAs": []}
            elif not e["qid"] and not e["sameAs"]:
                avis.append(f"{role} « {e['entite']} » sans QID au registre : posé sans sameAs")
            if e["entite"] in vus:
                continue
            vus.add(e["entite"])
            res.append(noeud_entite(e, glossaire))
        if len(res) > maxi:
            avis.append(f"{role} : {len(res)} entités, limité à {maxi}")
            res = res[:maxi]
        return res

    a = noeuds(about, "about", MAX_ABOUT)
    cles_about = {n.get("@id") or n.get("name") for n in a}
    m = [n for n in noeuds(mentions, "mentions", 10 ** 6) if (n.get("@id") or n.get("name")) not in cles_about]
    if len(m) > MAX_MENTIONS:
        avis.append(f"mentions : {len(m)} entités, limité aux {MAX_MENTIONS} plus saillantes")
        m = m[:MAX_MENTIONS]
    frag: dict = {}
    if url:
        frag["@id"] = url.split("#")[0] + "#webpage"
    if a:
        frag["about"] = a if len(a) > 1 else a[0]
    if m:
        frag["mentions"] = m
    return frag, avis


def mentions_auto(page: dict, entites: list[dict], exclure: list[str]) -> list[str]:
    """Les entités du registre visibles dans le contenu principal, de la plus à la moins saillante."""
    exclus = {norm(x) for x in exclure}
    visibles = {e["entite"]: formes(e) for e in entites
                if any(contient(page["texte_norm"], f) for f in formes(e)) and norm(e["entite"]) not in exclus}
    return [s["entite"] for s in saillance(page, visibles)]


def knows_about(entites: list[dict], glossaire: str | None = None) -> dict:
    retenues = [e for e in entites if (e.get("type") or "Thing") in ("Thing", "DefinedTerm")]
    return {"knowsAbout": [noeud_entite(e, glossaire) for e in retenues]}


# ─── wikidata ─────────────────────────────────────────────────────

API_WIKIDATA = "https://www.wikidata.org/w/api.php"


def candidats_wikidata(reponse: dict) -> list[dict]:
    return [{"qid": r.get("id", ""), "label": r.get("label", ""), "description": r.get("description", ""),
             "url": url_wikidata(r.get("id", ""))} for r in (reponse or {}).get("search", []) if r.get("id")]


def _hote(url: str) -> str:
    h = (urllib.parse.urlparse(url if "//" in url else "https://" + url).hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def enrichir_candidats(candidats: list[dict], entites_api: dict, domaine: str | None = None,
                       langue: str = "fr") -> list[dict]:
    """Ajoute le site officiel (P856), l'article Wikipédia et le verdict « site officiel = domaine ».

    Un homonyme n'est pas l'entité : quand on connaît le domaine de l'organisation,
    seul l'élément dont P856 pointe vers ce domaine est retenu."""
    ents = (entites_api or {}).get("entities", {})
    for c in candidats:
        e = ents.get(c["qid"], {})
        sites = []
        for claim in e.get("claims", {}).get("P856", []):
            v = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
            if isinstance(v, str):
                sites.append(v)
        c["site_officiel"] = sites
        titre = e.get("sitelinks", {}).get(f"{langue}wiki", {}).get("title")
        c["wikipedia"] = f"https://{langue}.wikipedia.org/wiki/{urllib.parse.quote(titre.replace(' ', '_'))}" \
            if titre else ""
        if domaine:
            c["correspond_au_site"] = any(_hote(s) == _hote(domaine) for s in sites)
    return candidats


def _get_json(params: dict, delai: float = 10.0) -> dict:
    url = API_WIKIDATA + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=delai) as rep:
        return json.loads(rep.read(2_000_000).decode("utf-8"))


def chercher_wikidata(label: str, langue: str = "fr", limite: int = 5, domaine: str | None = None) -> dict:
    """{candidats, erreur}. Jamais d'exception réseau : une panne se dit, elle ne plante pas la routine."""
    try:
        rep = _get_json({"action": "wbsearchentities", "search": label, "language": langue, "uselang": langue,
                         "type": "item", "limit": limite, "format": "json"})
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return {"candidats": [], "erreur": f"Wikidata injoignable ({str(getattr(exc, 'reason', exc))[:80]})"}
    cands = candidats_wikidata(rep)
    if cands:
        try:
            det = _get_json({"action": "wbgetentities", "ids": "|".join(c["qid"] for c in cands),
                             "props": "claims|sitelinks", "sitefilter": f"{langue}wiki", "format": "json"})
            enrichir_candidats(cands, det, domaine, langue)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            pass
    return {"candidats": cands, "erreur": None}


# ─── Affichage ────────────────────────────────────────────────────

def _cellule(s) -> str:
    return str(s if s is not None else "").replace("|", "\\|").replace("\n", " ")


def afficher_extraction(r: dict, tout: bool) -> None:
    print(f"# Triplets — {r['h1'] or r['titre'] or r['source']}\n")
    ts = [t for t in r["triplets"] if tout or (t["genre"] != "chiffre" and not t["sujet_implicite"])]
    print(f"{len(r['triplets'])} triplets candidats, {len(ts)} affichés · {r['mots']} mots\n")
    if ts:
        print("| Pos. | Sujet | Prédicat | Objet | Valeur | Genre |")
        print("|---:|---|---|---|---|---|")
        for t in ts:
            drapeau = (" (historique)" if t["historique"] else "") + \
                (" (sujet implicite)" if t["sujet_implicite"] else "")
            print(f"| {t['position']} | {_cellule(t['sujet'])} | {t['predicat']} | {_cellule(t['objet'])} | "
                  f"{_cellule(t['valeur_texte'])} | {t['genre']}{drapeau} |")
    if r["entites_jsonld"]:
        print("\n## Entités du JSON-LD\n\n| Rôle | Entité | Type | QID |\n|---|---|---|---|")
        for e in r["entites_jsonld"]:
            print(f"| {e['role']} | {_cellule(e['nom'])} | {e['type']} | {e['qid'] or '—'} |")
    else:
        print("\nAucune entité about/mentions/knowsAbout dans le JSON-LD.")
    if r["sujets_implicites_en_tete"]:
        print("\n## Sujet non nommé en tête de page (un moteur IA ne sait pas de quoi parle la phrase)\n")
        for p in r["sujets_implicites_en_tete"]:
            print(f"- {p}")
    if r["phrases_chargees"]:
        print("\n## Phrases à plusieurs faits (une idée par phrase)\n")
        for p in r["phrases_chargees"]:
            print(f"- {p}")


def afficher_verification(r: dict) -> None:
    print(f"# Triplets et entités — {r['page'] or r['source']}\n")
    ct = "—" if r["couverture_triplets"] is None else f"{r['couverture_triplets']} %"
    ce = "—" if r["couverture_entites"] is None else f"{r['couverture_entites']} %"
    print(f"- Triplets requis affirmés : **{ct}** ({len(r['triplets'])} requis, {r['en_tete']} en tête, "
          f"{r['contredits']} contredits)")
    print(f"- Entités visibles correctement balisées : **{ce}** ({r['entites_visibles']} entités du registre)\n")
    if r["triplets"]:
        print("| Statut | Sujet | Prédicat | Objet | Phrase |\n|---|---|---|---|---|")
        for s in r["triplets"]:
            st = s["statut"] + (" · en tête" if s["en_tete"] else "") + \
                (f" · trouvé {s['trouve']}" if s["trouve"] else "")
            print(f"| {st} | {_cellule(s['sujet'])} | {_cellule(s['predicat'])} | {_cellule(s['objet'])} | "
                  f"{_cellule(s['phrase'][:140])} |")
    if r["constats"]:
        print("\n## Entités\n")
        for c in r["constats"]:
            print(f"- [{c['gravite']}] **{c['entite']}** — {c['message']}")
    if r["saillance"]:
        print("\n## Saillance (heuristique)\n\n| Rang | Entité | Occurrences | Score |\n|---:|---|---:|---:|")
        for s in r["saillance"]:
            print(f"| {s['rang']} | {_cellule(s['entite'])} | {s['occurrences']} | {s['score']} |")


def afficher_coherence(r: dict) -> None:
    print(f"# Cohérence des faits — {r['pages']} pages\n")
    if not r["lignes"]:
        print("Aucune contradiction relevée.")
        return
    print("| Nature | Sujet | Prédicat | Valeurs relevées → pages |\n|---|---|---|---|")
    for l in r["lignes"]:
        vals = " ; ".join(f"**{v}** → {', '.join(Path(p).name or p for p in ps)}" for v, ps in l["valeurs"].items())
        print(f"| {l['nature']} | {_cellule(l['sujet'])} | {l['predicat']} | {_cellule(vals)} |")


# ─── Ligne de commande ────────────────────────────────────────────

def _registre(args) -> tuple[list[dict], list[dict]]:
    ent = args.entites
    if ent and not Path(ent).is_file() and ent.endswith(".csv") and Path(ent).with_suffix(".json").is_file():
        ent = str(Path(ent).with_suffix(".json"))
    return charger_entites(ent), charger_triplets(getattr(args, "triplets", None))


def main() -> int:
    ap = argparse.ArgumentParser(description="Triplets sémantiques, entités et cohérence des faits")
    sp = ap.add_subparsers(dest="cmd", required=True)

    e = sp.add_parser("extraire", help="triplets candidats et entités JSON-LD d'une page")
    e.add_argument("source", nargs="?", help="fichier HTML/MD/JSON/TXT ou URL")
    e.add_argument("--texte", help="texte brut à analyser à la place d'un fichier")
    e.add_argument("--tout", action="store_true", help="afficher aussi les chiffres isolés et sujets implicites")
    e.add_argument("--json", action="store_true")

    v = sp.add_parser("verifier", help="confronter une page au registre du projet")
    v.add_argument("source")
    v.add_argument("--page", help="identifiant de la page dans la colonne pages (défaut : tiré de la source)")
    v.add_argument("--entites", default="memoire/entites.csv")
    v.add_argument("--triplets", default="memoire/triplets.csv")
    v.add_argument("--tous", action="store_true", help="tous les triplets du registre, pas seulement ceux de la page")
    v.add_argument("--tete", type=int, default=TETE_MOTS, help="« en tête » = dans les N premiers mots")
    v.add_argument("--seuil", type=int, default=100, help="--strict : couverture minimale des triplets (%%)")
    v.add_argument("--strict", action="store_true", help="code 1 si contradiction, QID faux ou couverture < seuil")
    v.add_argument("--json", action="store_true")

    c = sp.add_parser("coherence", help="contradictions entre pages")
    c.add_argument("cibles", nargs="*", help="dossiers, fichiers ou URL")
    c.add_argument("--urls", help="fichier d'URL (une par ligne) ou CSV de crawl avec une colonne url")
    c.add_argument("--max", type=int, default=200, help="nombre maximal d'URL lues")
    c.add_argument("--entites", default="memoire/entites.csv")
    c.add_argument("--triplets", help="registre de référence (memoire/triplets.csv) : écarts à la valeur canonique")
    c.add_argument("--textes", action="store_true", help="signaler aussi les définitions formulées différemment")
    c.add_argument("--strict", action="store_true", help="code 1 s'il y a une contradiction")
    c.add_argument("--json", action="store_true")

    j = sp.add_parser("jsonld", help="fragment about/mentions depuis le registre")
    j.add_argument("--entites", default="memoire/entites.csv")
    j.add_argument("--about", default="", help="entités centrales, séparées par des virgules (3 au plus)")
    j.add_argument("--mentions", default="", help="entités citées, séparées par des virgules")
    j.add_argument("--depuis", help="page (fichier ou URL) : mentions = entités du registre visibles, par saillance")
    j.add_argument("--url", help="URL canonique : le fragment porte l'@id {url}#webpage")
    j.add_argument("--glossaire", help="@id du DefinedTermSet (page glossaire) pour les DefinedTerm")
    j.add_argument("--organisation", action="store_true", help="produire knowsAbout pour l'Organization")

    w = sp.add_parser("wikidata", help="chercher le QID d'un libellé (API publique, sans clé)")
    w.add_argument("label")
    w.add_argument("--langue", default="fr")
    w.add_argument("--limite", type=int, default=5)
    w.add_argument("--site", help="domaine officiel : retient l'élément dont P856 pointe vers lui")
    w.add_argument("--json", action="store_true")

    a = ap.parse_args()

    if a.cmd == "extraire":
        if not a.source and a.texte is None:
            ap.error("extraire : donnez une source ou --texte")
        r = extraire(lire_source(a.source, a.texte))
        print(json.dumps(r, ensure_ascii=False, indent=2)) if a.json else afficher_extraction(r, a.tout)
        return 0

    if a.cmd == "verifier":
        entites, triplets = _registre(a)
        if not entites and not triplets:
            print(f"  ! registre vide ({a.entites}, {a.triplets}) : seules les entités du JSON-LD sont lues",
                  file=sys.stderr)
        page = lire_source(a.source)
        r = verifier(page, entites, triplets, a.page if a.page is not None else a.source, a.tous, a.tete)
        print(json.dumps(r, ensure_ascii=False, indent=2)) if a.json else afficher_verification(r)
        if a.strict:
            bloque = r["contredits"] or any(c["gravite"] == "erreur" for c in r["constats"]) or \
                (r["couverture_triplets"] is not None and r["couverture_triplets"] < a.seuil)
            return 1 if bloque else 0
        return 0

    if a.cmd == "coherence":
        entites, _ = _registre(argparse.Namespace(entites=a.entites))
        registre = charger_triplets(a.triplets) if a.triplets else []
        cibles = list(a.cibles) + (urls_de(a.urls, a.max) if a.urls else [])
        if not cibles:
            ap.error("coherence : donnez un dossier, des fichiers, des URL ou --urls")
        r = coherence(pages_de(cibles), entites, registre, a.textes)
        print(json.dumps(r, ensure_ascii=False, indent=2)) if a.json else afficher_coherence(r)
        return 1 if a.strict and r["contradictions"] else 0

    if a.cmd == "jsonld":
        entites, _ = _registre(argparse.Namespace(entites=a.entites))
        if not entites:
            print(f"  ! registre vide ou absent ({a.entites}) : aucun sameAs ne sera posé", file=sys.stderr)
        if a.organisation:
            print(json.dumps(knows_about(entites, a.glossaire), ensure_ascii=False, indent=2))
            return 0
        about = [x.strip() for x in a.about.split(",") if x.strip()]
        mentions = [x.strip() for x in a.mentions.split(",") if x.strip()]
        if a.depuis:
            mentions += [m for m in mentions_auto(lire_source(a.depuis), entites, about) if m not in mentions]
        frag, avis = fragment_jsonld(entites, about, mentions, a.url, a.glossaire)
        for x in avis:
            print(f"  ! {x}", file=sys.stderr)
        print(json.dumps(frag, ensure_ascii=False, indent=2))
        return 0

    if a.cmd == "wikidata":
        r = chercher_wikidata(a.label, a.langue, a.limite, a.site)
        if a.json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
        elif r["erreur"]:
            print(f"✗ {r['erreur']} : inscrivez l'entité sans QID, à rechercher plus tard.")
        elif not r["candidats"]:
            print(f"Aucun élément Wikidata pour « {a.label} » : l'entité part sans sameAs.")
        else:
            print(f"| QID | Libellé | Description | Site officiel | Wikipédia |\n|---|---|---|---|---|")
            for c in r["candidats"]:
                ok = " ✅" if c.get("correspond_au_site") else ""
                print(f"| {c['qid']}{ok} | {_cellule(c['label'])} | {_cellule(c['description'])} | "
                      f"{_cellule(', '.join(c.get('site_officiel', [])))} | {c.get('wikipedia', '')} |")
            print("\nLisez les descriptions : le libellé ne suffit pas (homonymes). "
                  "Ligne à ajouter à memoire/entites.csv une fois le bon élément choisi :")
            c = next((x for x in r["candidats"] if x.get("correspond_au_site")), r["candidats"][0])
            csv.writer(sys.stdout, lineterminator="\n").writerow(
                [c["label"], "Thing", c["qid"], c.get("wikipedia", ""), c["description"], ""])
        return 2 if r["erreur"] else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
