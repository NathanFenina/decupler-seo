#!/usr/bin/env python3
"""Cherche sur Wikimedia Commons de vraies photos sous licence libre, avec l'auteur à créditer.

    python3 photos_libres.py "Lyon vieux port"
    python3 photos_libres.py "Annecy lac" --n 6 --largeur 1920 --json
    python3 photos_libres.py "Bordeaux place de la Bourse" --portrait

Pourquoi : une page qui parle d'un lieu réel (page ville, zone
d'intervention, article de terrain) et affiche un lieu inventé par un modèle
d'image montre un faux, et un lecteur du lieu le voit. Commons donne de
vraies photos, sous licence libre, avec l'auteur ; la licence exige de le
citer : la légende affiche auteur et licence.

Ce que le script écarte :
  - gravures, plans, cartes, blasons, logos, drapeaux, documents datés des
    XVIIe-XIXe siècles (on veut une photo, pas une estampe) ;
  - les formats autres que JPEG et PNG ;
  - les photos trop petites, et (sauf --portrait) celles qui ne sont pas
    franchement en paysage : un bandeau est large ;
  - toute licence qui n'est ni Creative Commons ni domaine public.

L'URL de travail est une vignette à la largeur demandée (`--largeur`) :
télécharger l'original fait vite répondre 429 par Wikimedia, et pèse
inutilement. Bibliothèque standard uniquement.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request

API = "https://commons.wikimedia.org/w/api.php?"
UA = {"User-Agent": "decupler-seo/3 (photos_libres.py; methode SEO open source)"}
REJET = re.compile(r"plan\b|carte|\bmap\b|gravure|engraving|lithograph|estampe|blason|coat of arms|logo|"
                   r"drapeau|flag|FMIB|\b1[6-8]\d\d\b", re.I)
LICENCES = re.compile(r"\bCC\b|CC[- ]BY|CC0|public domain|domaine public", re.I)


def requete_api(requete: str, n: int, largeur: int) -> dict:
    return {"action": "query", "format": "json", "generator": "search",
            "gsrsearch": f"filetype:bitmap {requete}", "gsrnamespace": "6", "gsrlimit": str(min(n * 4, 50)),
            "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime", "iiurlwidth": str(largeur)}


def _texte(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html or "")).strip()


def filtrer(reponse: dict, n: int = 12, mini_large: int = 1800, portrait: bool = False) -> list[dict]:
    """Réponse de l'API Commons → candidats utilisables, dans l'ordre de pertinence de la recherche."""
    pages = sorted((reponse.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    sortie = []
    for p in pages:
        titre = p.get("title", "")
        infos = (p.get("imageinfo") or [{}])[0]
        meta = infos.get("extmetadata") or {}
        if REJET.search(titre) or infos.get("mime") not in ("image/jpeg", "image/png"):
            continue
        l, h = int(infos.get("width") or 0), int(infos.get("height") or 0)
        if l < mini_large and not portrait:
            continue
        if not portrait and l <= h * 1.2:
            continue
        licence = _texte((meta.get("LicenseShortName") or {}).get("value", ""))
        if not LICENCES.search(licence):
            continue
        auteur = _texte((meta.get("Artist") or {}).get("value", ""))[:80] or "auteur non indiqué"
        sortie.append({
            "titre": titre, "largeur": l, "hauteur": h, "licence": licence, "auteur": auteur,
            "url": infos.get("thumburl") or infos.get("url"), "original": infos.get("url"),
            "page": "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(titre.replace(" ", "_"), safe=":/()"),
            "credit": f"Photo : {auteur}, {licence}, via Wikimedia Commons",
        })
        if len(sortie) >= n:
            break
    return sortie


def interroger(params: dict, essais: int = 4) -> dict:
    url = API + urllib.parse.urlencode(params)
    for essai in range(essais):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.load(r)
        except Exception:  # réseau, 429 : on attend et on réessaie
            if essai == essais - 1:
                raise
            time.sleep(2 ** essai)
    return {}


def main() -> int:
    ap = argparse.ArgumentParser(description="Photos libres de droits sur Wikimedia Commons, crédit compris")
    ap.add_argument("requete", nargs="+")
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--largeur", type=int, default=1920, help="largeur de la vignette téléchargée")
    ap.add_argument("--mini", type=int, default=1800, help="largeur minimale de l'original")
    ap.add_argument("--portrait", action="store_true", help="accepter les formats verticaux")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        reponse = interroger(requete_api(" ".join(a.requete), a.n, a.largeur))
    except Exception as exc:
        print(f"  ✗ Commons injoignable ({exc}). Aucune photo inventée à la place.", file=sys.stderr)
        return 1
    candidats = filtrer(reponse, a.n, a.mini, a.portrait)
    if a.json:
        print(json.dumps(candidats, ensure_ascii=False, indent=1))
        return 0
    if not candidats:
        print("  Aucune photo exploitable : élargir la requête (nom du quartier, du monument) ou --portrait.")
        return 0
    for c in candidats:
        print(f"  · {c['titre']}  {c['largeur']}×{c['hauteur']}\n    {c['url']}\n    {c['credit']}")
    print("\n  Afficher le crédit et la licence dans la légende : c'est la condition de la licence.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
