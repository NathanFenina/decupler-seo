#!/usr/bin/env python3
"""Score on-page /100 d'une page face à un mot-clé cible.

    python3 scripts/onpage_score.py https://exemple.com/page "mot clé cible"
    python3 scripts/onpage_score.py page.html "mot clé cible" --json

Barème : balises 25 · contenu 30 · GEO 20 · E-E-A-T 15 · maillage 10.
C'est le moteur de notation du skill seo-optimisation-onpage : il mesure,
le skill interprète et réécrit.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Dépendances manquantes. Lancez : pip install -r requirements.txt", file=sys.stderr)
    raise SystemExit(1)

AGENT = "ClaudeCodeSEODecupler/2.0 (+https://decupler.com)"


def sans_accents(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte.lower())
                   if unicodedata.category(c) != "Mn")


def contient(texte: str, cle: str) -> bool:
    """Comparaison tolérante aux accents et à la casse."""
    return sans_accents(cle) in sans_accents(texte)


def charger(source: str) -> str:
    chemin = Path(source)
    if chemin.exists():
        return chemin.read_text(encoding="utf-8")
    rep = requests.get(source, headers={"User-Agent": AGENT}, timeout=30)
    rep.raise_for_status()
    return rep.text


def feu(obtenu: int, maxi: int) -> str:
    ratio = obtenu / maxi if maxi else 0
    return "🟢" if ratio >= 0.8 else ("🟠" if ratio >= 0.5 else "🔴")


def noter(html: str, cle: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    criteres: list[dict] = []

    def ajouter(bloc, nom, points, maxi, constat):
        criteres.append({"bloc": bloc, "critere": nom, "points": points,
                         "max": maxi, "feu": feu(points, maxi), "constat": constat})

    # ── Bloc A · Balises et structure (25) ──────────────────────────
    title = (soup.title.string or "").strip() if soup.title else ""
    if not title:
        ajouter("A", "Title", 0, 6, "absent")
    else:
        pts, notes = 0, []
        trois_premiers = " ".join(title.split()[:3])
        if contient(trois_premiers, cle):
            pts += 3; notes.append("mot-clé dans les 3 premiers mots")
        elif contient(title, cle):
            pts += 1; notes.append("mot-clé présent mais tardif")
        else:
            notes.append("mot-clé absent")
        if 50 <= len(title) <= 60:
            pts += 3; notes.append(f"{len(title)} car., longueur idéale")
        elif 45 <= len(title) <= 70:
            pts += 2; notes.append(f"{len(title)} car., acceptable")
        else:
            notes.append(f"{len(title)} car., hors cible 50-60")
        ajouter("A", "Title", pts, 6, " · ".join(notes))

    tag = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    meta = (tag.get("content") or "").strip() if tag else ""
    if not meta:
        ajouter("A", "Meta description", 0, 4, "absente")
    else:
        pts = (2 if 150 <= len(meta) <= 160 else 1 if 120 <= len(meta) <= 170 else 0)
        pts += 2 if contient(meta, cle) else 0
        ajouter("A", "Meta description", pts, 4,
                f"{len(meta)} car., mot-clé {'présent' if contient(meta, cle) else 'absent'}")

    h1s = soup.find_all("h1")
    if len(h1s) == 1:
        texte_h1 = h1s[0].get_text(strip=True)
        pts = 5 if contient(texte_h1, cle) else 2
        ajouter("A", "H1", pts, 5, f"unique, mot-clé {'présent' if pts == 5 else 'absent'}")
    elif not h1s:
        ajouter("A", "H1", 0, 5, "absent")
    else:
        ajouter("A", "H1", 1, 5, f"{len(h1s)} H1 — il n'en faut qu'un")

    niveaux = [int(t.name[1]) for t in soup.find_all(re.compile("^h[1-6]$"))]
    sauts = sum(1 for a, b in zip(niveaux, niveaux[1:]) if b - a > 1)
    pts = 5 if not sauts and len(niveaux) >= 3 else (3 if sauts <= 1 else 1)
    ajouter("A", "Hiérarchie Hn", pts, 5,
            f"{len(niveaux)} titres, {sauts} saut(s) de niveau")

    canonical = soup.find("link", attrs={"rel": re.compile("^canonical$", re.I)})
    url_canon = canonical.get("href", "") if canonical else ""
    pts = 5 if url_canon and contient(url_canon, cle.split()[0]) else (3 if url_canon else 1)
    ajouter("A", "URL / canonical", pts, 5, url_canon or "canonical absente")

    # ── Bloc B · Contenu et sémantique (30) ─────────────────────────
    # Le JSON-LD est extrait AVANT de retirer les <script> : sinon il
    # disparaît et le bloc E le compte à tort comme absent.
    jsonld = " ".join(s.get_text() for s in soup.find_all(
        "script", attrs={"type": "application/ld+json"}))

    for balise in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        balise.decompose()
    texte = soup.get_text(" ", strip=True)
    mots = texte.split()
    nb_mots = len(mots)
    debut = " ".join(mots[:100])
    h2s = " ".join(h.get_text() for h in soup.find_all("h2"))
    fin = " ".join(mots[-150:])

    zones = {"H1": bool(h1s) and contient(h1s[0].get_text(), cle),
             "100 premiers mots": contient(debut, cle),
             "un H2": contient(h2s, cle),
             "conclusion": contient(fin, cle)}
    couvertes = sum(zones.values())
    occurrences = sans_accents(texte).count(sans_accents(cle))
    densite = occurrences / nb_mots * 100 if nb_mots else 0
    if densite > 4:
        pts = 1
        constat = f"{occurrences} occurrences ({densite:.1f} %) — bourrage manifeste"
    else:
        pts = round(couvertes / 4 * 6)
        manquantes = [z for z, ok in zones.items() if not ok]
        constat = (f"{occurrences} occurrences, zones couvertes {couvertes}/4"
                   + (f" — manque : {', '.join(manquantes)}" if manquantes else ""))
    ajouter("B", "Présence du mot-clé", pts, 6, constat)

    termes = [m.lower() for m in re.findall(r"\b[a-zà-ÿ]{5,}\b", texte.lower())]
    uniques = len(set(termes))
    pts = 8 if uniques > 300 else (6 if uniques > 180 else (4 if uniques > 90 else 2))
    ajouter("B", "Richesse sémantique", pts, 8, f"{uniques} termes distincts")

    pts = 6 if nb_mots >= 1200 else (4 if nb_mots >= 700 else (2 if nb_mots >= 300 else 0))
    ajouter("B", "Profondeur", pts, 6,
            f"{nb_mots} mots" + (" — contenu mince" if nb_mots < 300 else ""))

    phrases = [p for p in re.split(r"[.!?]+", texte) if len(p.split()) > 2]
    moy = sum(len(p.split()) for p in phrases) / len(phrases) if phrases else 0
    pts = 5 if moy <= 20 else (3 if moy <= 28 else 1)
    ajouter("B", "Lisibilité", pts, 5, f"{moy:.0f} mots/phrase en moyenne")

    a_tableau = bool(soup.find("table"))
    a_liste = len(soup.find_all(["ul", "ol"])) >= 2
    # Pas de \b final : un symbole comme € ou % n'est pas un caractère de mot,
    # donc \b après lui ne se déclenche jamais et la détection échouerait.
    nb_chiffres = len(re.findall(
        r"\d+(?:[  .,]\d+)*\s*(?:%|€|\$|k€|ans?\b|jours?\b|heures?\b|min\b|mois\b)",
        texte, re.I))
    a_chiffres = nb_chiffres >= 3
    pts = sum([2 if a_chiffres else 0, 2 if a_tableau else 0, 1 if a_liste else 0])
    ajouter("B", "Originalité et preuves", pts, 5,
            f"{nb_chiffres} donnée(s) chiffrée(s) · tableau {'oui' if a_tableau else 'non'}"
            f" · listes {'oui' if a_liste else 'non'}")

    # ── Bloc C · GEO et citabilité (20) ─────────────────────────────
    paragraphes = [p.get_text(strip=True) for p in soup.find_all("p")]
    reponse = next((p for p in paragraphes[:4] if 30 <= len(p.split()) <= 90), "")
    pts = 6 if reponse else (3 if paragraphes and len(paragraphes[0].split()) >= 20 else 0)
    ajouter("C", "Réponse directe", pts, 6,
            f"{len(reponse.split())} mots en tête" if reponse
            else "aucun paragraphe de 40-60 mots en ouverture")

    pts = min(4, len(soup.find_all(["ul", "ol", "table"])))
    ajouter("C", "Structure extractible", pts, 4,
            f"{len(soup.find_all(['ul', 'ol', 'table']))} éléments structurés")

    definitions = len(re.findall(r"\b(est un|est une|désigne|consiste à|se définit)\b", texte, re.I))
    pts = 3 if definitions >= 2 else (2 if definitions == 1 else 0)
    ajouter("C", "Définitions autonomes", pts, 3, f"{definitions} formulation(s) de définition")

    a_faq = bool(soup.find(string=re.compile(r"FAQ|questions fréquentes", re.I))) \
        or bool(soup.find_all("details"))
    ajouter("C", "FAQ", 4 if a_faq else 0, 4, "présente" if a_faq else "absente")

    sources = len([a for a in soup.find_all("a", href=True)
                   if a["href"].startswith("http") and "cite" not in a.get("class", [])])
    pts = 3 if a_chiffres and sources >= 2 else (1 if a_chiffres else 0)
    ajouter("C", "Données sourcées", pts, 3,
            f"{sources} liens externes, chiffres {'présents' if a_chiffres else 'absents'}")

    # ── Bloc D · E-E-A-T (15) ───────────────────────────────────────
    # `jsonld` a été capturé plus haut, avant la suppression des <script>.
    a_auteur = bool(re.search(r"\b(par|rédigé par|auteur|author)\b", texte[:2000], re.I)) \
        or '"Person"' in jsonld
    ajouter("D", "Auteur identifié", 4 if a_auteur else 0, 4,
            "signature détectée" if a_auteur else "aucune signature")

    experience = len(re.findall(
        r"\b(nous avons|j'ai|notre expérience|sur \d+|nos \d+|testé|constaté|observé)\b",
        texte, re.I))
    pts = 4 if experience >= 3 else (2 if experience >= 1 else 0)
    ajouter("D", "Expérience de première main", pts, 4, f"{experience} marqueur(s)")

    externes = len([a for a in soup.find_all("a", href=True) if a["href"].startswith("http")])
    pts = 3 if externes >= 3 else (2 if externes >= 1 else 0)
    ajouter("D", "Sources externes", pts, 3, f"{externes} liens sortants")

    a_date = bool(soup.find("time")) or bool(re.search(r"\b(mis à jour|publié le)\b", texte, re.I)) \
        or "datePublished" in jsonld
    ajouter("D", "Dates affichées", 2 if a_date else 0, 2,
            "présentes" if a_date else "absentes")

    a_confiance = bool(re.search(r"\b(contact|mentions légales|à propos)\b", html, re.I))
    ajouter("D", "Transparence", 2 if a_confiance else 0, 2,
            "liens de confiance présents" if a_confiance else "aucun")

    # ── Bloc E · Maillage et technique (10) ─────────────────────────
    tous_liens = soup.find_all("a", href=True)
    internes = [a for a in tous_liens if not a["href"].startswith("http")]
    vides = sum(1 for a in internes
                if a.get_text(strip=True).lower() in
                {"", "cliquez ici", "en savoir plus", "ici", "lire la suite", "voir"})
    pts = 4 if len(internes) >= 3 and vides == 0 else (2 if len(internes) >= 3 else 1 if internes else 0)
    ajouter("E", "Liens internes", pts, 4,
            f"{len(internes)} liens, {vides} ancre(s) vide(s)")

    ajouter("E", "Liens externes", 2 if externes >= 1 else 0, 2, f"{externes} liens")

    images = soup.find_all("img")
    sans_alt = sum(1 for i in images if not (i.get("alt") or "").strip())
    pts = 2 if images and sans_alt == 0 else (1 if images else 0)
    ajouter("E", "Images", pts, 2,
            f"{len(images)} images, {sans_alt} sans alt" if images else "aucune image")

    ajouter("E", "Schema JSON-LD", 2 if jsonld else 0, 2,
            "présent" if jsonld else "absent")

    # ── Agrégation ──────────────────────────────────────────────────
    blocs = {}
    for c in criteres:
        b = blocs.setdefault(c["bloc"], {"points": 0, "max": 0})
        b["points"] += c["points"]
        b["max"] += c["max"]

    total = sum(b["points"] for b in blocs.values())
    return {"score": total, "criteres": criteres, "blocs": blocs, "mots": nb_mots}


NOMS_BLOCS = {
    "A": "Balises et structure", "B": "Contenu et sémantique",
    "C": "GEO et citabilité", "D": "E-E-A-T", "E": "Maillage et technique",
}


def afficher(res: dict, cle: str) -> None:
    score = res["score"]
    verdict = ("🟢 publiable" if score >= 85 else "🟢 bon" if score >= 70
               else "🟠 à retravailler" if score >= 50
               else "🔴 réécriture partielle" if score >= 30 else "🔴 repartir de zéro")

    print(f"\n{'═' * 62}")
    print(f"  SCORE ON-PAGE : {score}/100   {verdict}")
    print(f"  Mot-clé cible : « {cle} »   ·   {res['mots']} mots")
    print(f"{'═' * 62}\n")

    for lettre in "ABCDE":
        b = res["blocs"].get(lettre)
        if not b:
            continue
        print(f"  {lettre} · {NOMS_BLOCS[lettre]:<26} "
              f"{b['points']:>2}/{b['max']:<3} {feu(b['points'], b['max'])}")
    print()

    a_corriger = [c for c in res["criteres"] if c["feu"] != "🟢"]
    if a_corriger:
        print("─── À corriger, par priorité ───\n")
        for c in sorted(a_corriger, key=lambda x: x["points"] / x["max"]):
            print(f"  {c['feu']} {c['critere']} — {c['points']}/{c['max']}")
            print(f"     {c['constat']}\n")
    else:
        print("  Tous les critères sont au vert.\n")


def main() -> int:
    p = argparse.ArgumentParser(description="Score on-page /100")
    p.add_argument("source", help="URL ou fichier HTML")
    p.add_argument("motcle", help="mot-clé cible")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    res = noter(charger(args.source), args.motcle)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        afficher(res, args.motcle)
    return 0


if __name__ == "__main__":
    sys.exit(main())
