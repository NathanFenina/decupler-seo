#!/usr/bin/env python3
"""Duplication entre les pages d'un même lot : phrases communes et part de contenu unique.

    python3 similarite_lot.py contenus/villes/                 # tous les .html/.md du dossier
    python3 similarite_lot.py a.html b.html c.html --strict    # code 1 au-delà des seuils
    python3 similarite_lot.py contenus/villes/ --json

Un lot de pages construites sur un même gabarit (pages villes, fiches
services, pages programmatiques) se juge comme un lot : si les pages se
répètent, c'est tout le lot qui est classé comme du contenu dupliqué. Une
relecture ne voit pas la redite ; une comparaison phrase à phrase, si.

Deux mesures :
  - par paire de pages, le nombre de phrases communes (phrases d'au moins
    8 mots, comparées sans casse ni accents) — seuil : 4 ;
  - par page, la part de son texte qui ne se retrouve dans aucune autre
    page du lot — seuil : 60 %.

Ce qui est identique par construction (en-tête, bande de logos, CTA final,
bloc auteur) n'est pas du contenu : marquez son élément racine avec
`data-gabarit="commun"`, il est retiré avant la comparaison. Sans ce
marquage, l'alerte se déclenche sur le chrome et on finit par l'ignorer —
alors qu'elle est là pour attraper la vraie redite éditoriale.

Bibliothèque standard uniquement.
"""

from __future__ import annotations

import argparse
import html as html_lib
import itertools
import json
import re
import sys
import unicodedata
from pathlib import Path

MOTS_MIN_PHRASE = 8
SEUIL_PAIRE = 4          # phrases communes tolérées entre deux pages
UNIQUE_MIN = 60.0        # % du texte d'une page absent de toutes les autres
EXTENSIONS = {".html", ".htm", ".md", ".txt"}
MARQUEUR = re.compile(r"""data-gabarit\s*=\s*["']commun["']""", re.I)
OUVRANTE = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)\b[^>]*?(/?)>")
VIDES = {"br", "img", "hr", "input", "meta", "link", "source", "wbr", "area", "col", "embed", "track"}


def retirer_communs(html: str) -> str:
    """Retire chaque élément marqué data-gabarit="commun", enfants compris."""
    while m := MARQUEUR.search(html):
        debut = html.rfind("<", 0, m.start())
        balise = OUVRANTE.match(html, debut)
        if not balise:
            break
        nom, profondeur, fin = balise.group(2).lower(), 0, len(html)
        for t in OUVRANTE.finditer(html, debut):
            if t.group(2).lower() != nom or t.group(3) or nom in VIDES:
                continue
            profondeur += -1 if t.group(1) else 1
            if profondeur == 0:
                fin = t.end()
                break
        html = html[:debut] + " " + html[fin:]
    return html


def texte_visible(contenu: str, est_html: bool) -> str:
    if est_html:
        contenu = retirer_communs(contenu)
        contenu = re.sub(r"<(script|style|template)\b.*?</\1>", " ", contenu, flags=re.S | re.I)
        contenu = re.sub(r"<!--.*?-->", " ", contenu, flags=re.S)
        contenu = re.sub(r"<(br|/p|/li|/h[1-6]|/div|/td|/th|/dt|/dd|/summary)\b[^>]*>", ". ", contenu, flags=re.I)
        contenu = html_lib.unescape(re.sub(r"<[^>]+>", " ", contenu))
    else:
        contenu = re.sub(r"^---\n.*?\n---\n", "", contenu, flags=re.S)
        contenu = re.sub(r"[#*_>`|\[\]()]", " ", contenu)
        contenu = re.sub(r"\n\s*\n", ". ", contenu)
    return re.sub(r"\s+", " ", contenu.replace(" ", " ")).strip()


def normaliser(phrase: str) -> str:
    phrase = unicodedata.normalize("NFKD", phrase.lower())
    phrase = "".join(c for c in phrase if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", phrase))


def phrases(texte: str) -> dict[str, int]:
    """Phrases d'au moins MOTS_MIN_PHRASE mots, normalisées → nombre de mots."""
    resultat = {}
    for brute in re.split(r"(?<=[.!?…])\s+", texte):
        norme = normaliser(brute)
        n = len(norme.split())
        if n >= MOTS_MIN_PHRASE:
            resultat[norme] = n
    return resultat


def analyser(pages: dict[str, str], seuil_paire: int = SEUIL_PAIRE, unique_min: float = UNIQUE_MIN) -> dict:
    """pages : {nom: texte visible}. Paires au-dessus du seuil et part unique par page."""
    ph = {nom: phrases(t) for nom, t in pages.items()}
    paires = []
    for a, b in itertools.combinations(sorted(ph), 2):
        communes = sorted(set(ph[a]) & set(ph[b]))
        if communes:
            paires.append({"pages": [a, b], "communes": len(communes), "exemples": communes[:3],
                           "alerte": len(communes) >= seuil_paire})
    paires.sort(key=lambda p: -p["communes"])
    par_page = []
    for nom in sorted(ph):
        ailleurs = set().union(*(set(ph[x]) for x in ph if x != nom)) if len(ph) > 1 else set()
        total = sum(ph[nom].values())
        repete = sum(n for p, n in ph[nom].items() if p in ailleurs)
        unique = round(100 * (total - repete) / total, 1) if total else 100.0
        par_page.append({"page": nom, "mots_en_phrases": total, "unique_pct": unique,
                         "alerte": bool(total) and unique < unique_min})
    bloque = any(p["alerte"] for p in paires) or any(p["alerte"] for p in par_page)
    return {"pages": len(ph), "seuil_paire": seuil_paire, "unique_min": unique_min,
            "paires": paires, "par_page": par_page, "bloquant": bloque}


def fichiers(cibles: list[str]) -> list[Path]:
    trouves = []
    for c in cibles:
        p = Path(c)
        if p.is_dir():
            trouves += sorted(x for x in p.rglob("*") if x.suffix.lower() in EXTENSIONS
                              and not any(part.startswith(".") for part in x.parts))
        elif p.is_file():
            trouves.append(p)
        else:
            print(f"  ! introuvable : {c}", file=sys.stderr)
    return trouves


def main() -> int:
    ap = argparse.ArgumentParser(description="Phrases communes et contenu unique dans un lot de pages")
    ap.add_argument("cibles", nargs="+", help="fichiers ou dossiers (.html, .md, .txt)")
    ap.add_argument("--seuil", type=int, default=SEUIL_PAIRE, help="phrases communes tolérées par paire")
    ap.add_argument("--unique-min", type=float, default=UNIQUE_MIN, help="%% de contenu unique exigé par page")
    ap.add_argument("--strict", action="store_true", help="code de sortie 1 au-delà des seuils")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    liste = fichiers(a.cibles)
    if len(liste) < 2:
        print("  ✗ Il faut au moins deux pages pour comparer un lot.", file=sys.stderr)
        return 1
    pages = {str(f): texte_visible(f.read_text(encoding="utf-8", errors="replace"),
                                   f.suffix.lower() in {".html", ".htm"}) for f in liste}
    res = analyser(pages, a.seuil, a.unique_min)

    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        print(f"\n  {res['pages']} pages · seuils : {a.seuil} phrases communes par paire, "
              f"{a.unique_min:g} % de contenu unique par page\n")
        for p in res["par_page"]:
            print(f"  {'✗' if p['alerte'] else '✓'} {p['unique_pct']:5.1f} % unique  {p['page']}")
        alertes = [p for p in res["paires"] if p["alerte"]]
        if alertes:
            print(f"\n  {len(alertes)} paire(s) au-delà du seuil :")
            for p in alertes[:15]:
                print(f"    · {p['communes']} phrases communes : {p['pages'][0]}  ↔  {p['pages'][1]}")
                for ex in p["exemples"]:
                    print(f"        « {ex[:110]} »")
        elif res["paires"]:
            pire = res["paires"][0]
            print(f"\n  pire paire : {pire['communes']} phrase(s) commune(s), sous le seuil.")
        print("\n  " + ("✗ Lot trop répétitif : réécrivez ce qui est propre à chaque page." if res["bloquant"]
                        else "✓ Lot assez différencié.") + "\n")
    return 1 if (a.strict and res["bloquant"]) else 0


if __name__ == "__main__":
    sys.exit(main())
