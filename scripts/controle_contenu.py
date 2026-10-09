#!/usr/bin/env python3
"""Contrôle qualité des contenus avant publication — bloquant.

    python3 controle_contenu.py contenus/
    python3 controle_contenu.py page.html article.md src/content/fr/guide.json
    python3 controle_contenu.py contenus/ --json

Échoue (code 1) sur toute erreur. Les règles d'un projet s'ajoutent à celles
de la méthode, dans decupler-seo.config.yml :

    regles:
      interdits:            # expressions propres au client, en expressions régulières
        - "\\bn°\\s?1\\b"
        - "leader du marché"

Pourquoi un script plutôt qu'une consigne : une consigne s'oublie dans une
longue session ou une routine ; un script qui renvoie 1 arrête la publication.

Vérifie : expressions interdites (tics d'écriture générée, promesses et
preuves invérifiables, règles du projet), textes provisoires oubliés,
longueurs de title et meta, H1 unique, alt des images, sources en https.
Formats : .html, .md, .json (toutes les chaînes du JSON sont inspectées).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import lire_liste  # noqa: E402

# ─── Règles de la méthode ─────────────────────────────────────────
# Tics d'écriture générée : ils signalent un texte que personne n'a relu.
TICS = [
    r"il est important de noter", r"dans un monde en constante évolution",
    r"dans le monde d'aujourd'hui", r"à l'ère du numérique", r"de nos jours",
    r"plongeons dans", r"plonger dans l'univers", r"exploiter tout le potentiel",
    r"n'hésitez pas à", r"en conclusion, il apparaît", r"que vous soyez .{3,40} ou",
    r"in today's fast-paced", r"let's dive", r"it is important to note", r"unlock the power",
    r"in the ever-evolving",
]
# Promesses et preuves qui ne se vérifient pas : risque juridique et de crédibilité.
PROMESSES = [
    r"\b(n°\s?1|numéro un|number one)\b", r"\bleader (du marché|incontesté)\b",
    r"\bgaranti(e|s)? (à|a) 100\s?%", r"\brésultats? garanti", r"\bguaranteed results?\b",
    r"\+\s?\d{2,}[\s ]?(clients|entreprises|sociétés|companies)\b",
]
# Textes provisoires : ne doivent jamais partir en production.
PROVISOIRES = [r"\{\{[^}]+\}\}", r"\[à compléter\]", r"\[TODO\]", r"\bTODO\b", r"lorem ipsum",
               r"\[insérer", r"\bXXX\b"]

TITLE_MIN, TITLE_MAX = 30, 65
META_MIN, META_MAX = 110, 165


class Rapport:
    def __init__(self) -> None:
        self.erreurs: list[str] = []
        self.avertissements: list[str] = []

    def err(self, f: Path, m: str) -> None:
        self.erreurs.append(f"{f}: {m}")

    def avert(self, f: Path, m: str) -> None:
        self.avertissements.append(f"{f}: {m}")


def compiler(motifs: list[str]) -> list[re.Pattern]:
    compiles = []
    for m in motifs:
        try:
            compiles.append(re.compile(m, re.I))
        except re.error as exc:
            print(f"  ! motif ignoré, expression invalide « {m} » : {exc}", file=sys.stderr)
    return compiles


def verifier_texte(f: Path, texte: str, r: Rapport, interdits: list[re.Pattern]) -> None:
    for motif in compiler(PROVISOIRES):
        if m := motif.search(texte):
            r.err(f, f"texte provisoire oublié : « {m.group(0)} »")
    for motif in compiler(PROMESSES):
        if m := motif.search(texte):
            r.err(f, f"promesse ou preuve invérifiable : « {m.group(0)} »")
    for motif in interdits:
        if m := motif.search(texte):
            r.err(f, f"interdit du projet : « {m.group(0)} »")
    tics = [m.group(0) for motif in compiler(TICS) if (m := motif.search(texte))]
    if tics:
        r.avert(f, "tournures d'écriture générée : " + ", ".join(f"« {t} »" for t in tics[:4]))


def verifier_longueur(f: Path, nom: str, valeur: str, mini: int, maxi: int, r: Rapport) -> None:
    n = len(valeur.strip())
    if n == 0:
        r.err(f, f"{nom} vide")
    elif n > maxi:
        r.err(f, f"{nom} trop long ({n} car., max {maxi}) : tronqué dans la SERP")
    elif n < mini:
        r.avert(f, f"{nom} court ({n} car., conseillé ≥ {mini})")


def verifier_html(f: Path, html: str, r: Rapport, interdits: list[re.Pattern]) -> None:
    # Le <title> d'un SVG inline (titre accessible d'un graphique, info-bulle
    # d'une barre) n'est pas le title de la page : on l'écarte avant de chercher.
    sans_svg = re.sub(r"<svg\b.*?</svg>", " ", html, flags=re.S | re.I)
    if m := re.search(r"<title[^>]*>(.*?)</title>", sans_svg, re.S | re.I):
        verifier_longueur(f, "title", re.sub(r"\s+", " ", m.group(1)), TITLE_MIN, TITLE_MAX, r)
    if m := re.search(r'<meta[^>]+name=["\']description["\'][^>]*content=["\']([^"\']*)', html, re.I):
        verifier_longueur(f, "meta description", m.group(1), META_MIN, META_MAX, r)
    nb_h1 = len(re.findall(r"<h1[\s>]", html, re.I))
    if nb_h1 > 1:
        r.err(f, f"{nb_h1} balises H1 — il n'en faut qu'une")
    for img in re.findall(r"<img\b[^>]*>", html, re.I):
        if not re.search(r'\balt=["\'][^"\']+["\']', img) and 'alt=""' not in img:
            r.err(f, f"image sans attribut alt : {img[:80]}")
    for lien in re.findall(r'href=["\'](http://[^"\']+)', html, re.I):
        if not re.match(r"http://(localhost|127\.)", lien):
            r.avert(f, f"lien en http (pas https) : {lien[:80]}")
    texte = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S | re.I)
    verifier_texte(f, re.sub(r"<[^>]+>", " ", texte), r, interdits)


def verifier_markdown(f: Path, md: str, r: Rapport, interdits: list[re.Pattern]) -> None:
    if md.startswith("---"):
        entete = md.split("---", 2)[1]
        for cle, (mini, maxi) in {"title": (TITLE_MIN, TITLE_MAX),
                                  "description": (META_MIN, META_MAX)}.items():
            if m := re.search(rf"^{cle}:\s*[\"']?(.+?)[\"']?\s*$", entete, re.M):
                verifier_longueur(f, cle, m.group(1), mini, maxi, r)
    corps = md.split("---", 2)[2] if md.startswith("---") else md
    if len(re.findall(r"^# ", corps, re.M)) > 1:
        r.err(f, "plusieurs titres de niveau 1 (#)")
    for lien in re.findall(r"\]\((http://[^)]+)\)", corps):
        r.avert(f, f"lien en http (pas https) : {lien[:80]}")
    verifier_texte(f, corps, r, interdits)


def chaines(objet, chemin: str = "") -> list[tuple[str, str]]:
    if isinstance(objet, str):
        return [(chemin, objet)]
    if isinstance(objet, dict):
        return [c for k, v in objet.items() for c in chaines(v, f"{chemin}.{k}" if chemin else k)]
    if isinstance(objet, list):
        return [c for i, v in enumerate(objet) for c in chaines(v, f"{chemin}[{i}]")]
    return []


# Clés qui portent le title et la meta dans les contenus JSON des sites en code.
CLES_TITLE = {"metatitle", "seotitle", "title_seo", "meta_title"}
CLES_META = {"metadescription", "seodescription", "meta_description", "description_seo"}


def verifier_json(f: Path, brut: str, r: Rapport, interdits: list[re.Pattern]) -> None:
    try:
        donnees = json.loads(brut)
    except json.JSONDecodeError as exc:
        r.err(f, f"JSON invalide : {exc}")
        return
    toutes = chaines(donnees)
    for chemin, valeur in toutes:
        feuille = chemin.split(".")[-1].split("[")[0].lower()
        # « title » seul désigne aussi un titre de section : on ne le contrôle
        # comme balise que sous un parent meta ou seo (meta.title, seo.title).
        parent = chemin.lower().rsplit(".", 2)[-2] if chemin.count(".") >= 1 else ""
        if feuille in CLES_TITLE or (parent in {"meta", "seo"} and feuille == "title"):
            verifier_longueur(f, chemin, valeur, TITLE_MIN, TITLE_MAX, r)
        elif feuille in CLES_META or (parent in {"meta", "seo"} and feuille == "description"):
            verifier_longueur(f, chemin, valeur, META_MIN, META_MAX, r)
        if valeur.startswith("http://") and not valeur.startswith(("http://localhost", "http://127.")):
            r.avert(f, f"{chemin} : URL en http (pas https)")
    verifier_texte(f, "\n".join(v for _, v in toutes), r, interdits)


def fichiers(cibles: list[str]) -> list[Path]:
    trouves = []
    for c in cibles:
        p = Path(c)
        if p.is_dir():
            trouves += sorted(x for x in p.rglob("*") if x.suffix in {".html", ".htm", ".md", ".json"}
                              and not any(part.startswith(".") or part == "node_modules" for part in x.parts))
        elif p.is_file():
            trouves.append(p)
        else:
            print(f"  ! introuvable : {c}", file=sys.stderr)
    return trouves


def main() -> int:
    ap = argparse.ArgumentParser(description="Contrôle qualité des contenus (bloquant)")
    ap.add_argument("cibles", nargs="+", help="fichiers ou dossiers")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="les avertissements bloquent aussi")
    a = ap.parse_args()

    interdits = compiler(lire_liste("regles.interdits"))
    r = Rapport()
    liste = fichiers(a.cibles)
    for f in liste:
        brut = f.read_text(encoding="utf-8", errors="replace")
        {".html": verifier_html, ".htm": verifier_html, ".md": verifier_markdown,
         ".json": verifier_json}[f.suffix](f, brut, r, interdits)

    bloque = bool(r.erreurs) or (a.strict and bool(r.avertissements))
    if a.json:
        print(json.dumps({"fichiers": len(liste), "erreurs": r.erreurs,
                          "avertissements": r.avertissements, "bloquant": bloque}, ensure_ascii=False, indent=1))
    else:
        print(f"\n  {len(liste)} fichier(s) · {len(r.erreurs)} erreur(s) · {len(r.avertissements)} avertissement(s)"
              f" · {len(interdits)} règle(s) propre(s) au projet\n")
        for e in r.erreurs:
            print(f"  ✗ {e}")
        for w in r.avertissements:
            print(f"  ! {w}")
        print("\n  " + ("✗ BLOQUÉ — corrigez avant de publier." if bloque else "✓ Publiable.") + "\n")
    return 1 if bloque else 0


if __name__ == "__main__":
    sys.exit(main())
