#!/usr/bin/env python3
"""Audit des images d'une page — poids, format, dimensions, alt, lazy loading.

    python3 scripts/audit_images.py https://exemple.com/page
    python3 scripts/audit_images.py https://exemple.com/page --exporter images.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Dépendances manquantes : pip install -r requirements.txt", file=sys.stderr)
    raise SystemExit(1)

AGENT = "ClaudeCodeSEODecupler/2.0 (+https://decupler.com)"
MODERNES = {"webp", "avif", "svg"}
SEUIL_KO = 150
SEUIL_HERO_KO = 250


def format_de(url: str) -> str:
    chemin = urlparse(url).path.lower()
    for ext in ("avif", "webp", "svg", "jpeg", "jpg", "png", "gif"):
        if chemin.endswith("." + ext):
            return "jpeg" if ext == "jpg" else ext
    return "inconnu"


def poids(url: str) -> int:
    """Poids en Ko. HEAD d'abord, GET partiel en repli."""
    try:
        rep = requests.head(url, headers={"User-Agent": AGENT}, timeout=15, allow_redirects=True)
        taille = rep.headers.get("Content-Length")
        if taille:
            return int(taille) // 1024
        rep = requests.get(url, headers={"User-Agent": AGENT}, timeout=20, stream=True)
        return len(rep.content) // 1024
    except (requests.RequestException, ValueError):
        return -1


def main() -> int:
    p = argparse.ArgumentParser(description="Audit des images")
    p.add_argument("url")
    p.add_argument("--exporter", default="images.csv")
    p.add_argument("--sans-poids", action="store_true",
                   help="ne télécharge pas les images (plus rapide, pas de poids)")
    args = p.parse_args()

    rep = requests.get(args.url, headers={"User-Agent": AGENT}, timeout=30)
    rep.raise_for_status()
    soup = BeautifulSoup(rep.text, "html.parser")
    images = soup.find_all("img")

    if not images:
        print("\n  Aucune image trouvée sur cette page.\n")
        return 0

    lignes, total_ko, problemes = [], 0, []

    for rang, img in enumerate(images, 1):
        src = img.get("src") or img.get("data-src") or ""
        if not src or src.startswith("data:"):
            continue
        url_img = urljoin(args.url, src)
        est_hero = rang <= 2  # approximation : les 2 premières images du DOM

        ko = -1 if args.sans_poids else poids(url_img)
        if ko > 0:
            total_ko += ko

        ligne = {
            "url": url_img,
            "format": format_de(url_img),
            "poids_ko": ko if ko >= 0 else "",
            "width": img.get("width", ""),
            "height": img.get("height", ""),
            "alt": (img.get("alt") or "").strip(),
            "loading": img.get("loading", ""),
            "fetchpriority": img.get("fetchpriority", ""),
            "srcset": "oui" if img.get("srcset") else "non",
            "rang": rang,
        }

        soucis = []
        if ligne["format"] not in MODERNES and ligne["format"] != "inconnu":
            soucis.append(f"format {ligne['format']} — passez en WebP ou AVIF")
        seuil = SEUIL_HERO_KO if est_hero else SEUIL_KO
        if ko > seuil:
            soucis.append(f"{ko} Ko, au-dessus du seuil de {seuil} Ko")
        if not ligne["width"] or not ligne["height"]:
            soucis.append("dimensions absentes — cause directe de CLS")
        if not ligne["alt"]:
            soucis.append("alt manquant")
        elif len(ligne["alt"].split()) > 15:
            soucis.append("alt trop long, probablement bourré de mots-clés")
        if est_hero and ligne["loading"] == "lazy":
            soucis.append("🔴 loading=lazy sur une image du premier écran — "
                          "retarde le LCP de plusieurs centaines de ms")
        if not est_hero and ligne["loading"] != "lazy":
            soucis.append("loading=lazy absent sur une image hors premier écran")
        if est_hero and not ligne["fetchpriority"]:
            soucis.append("fetchpriority=\"high\" recommandé sur l'image LCP")
        if not img.get("srcset") and ko > 100:
            soucis.append("pas de srcset — le mobile télécharge l'image desktop")

        ligne["problemes"] = " · ".join(soucis)
        lignes.append(ligne)
        if soucis:
            problemes.append((url_img, soucis))

    with open(args.exporter, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
        w.writeheader()
        w.writerows(lignes)

    print(f"\n{'═' * 62}")
    print(f"  {len(lignes)} images" + (f" · {total_ko} Ko au total" if total_ko else ""))
    print(f"{'═' * 62}\n")

    sans_alt = sum(1 for l in lignes if not l["alt"])
    sans_dim = sum(1 for l in lignes if not l["width"] or not l["height"])
    anciennes = sum(1 for l in lignes if l["format"] not in MODERNES and l["format"] != "inconnu")

    for libelle, n in [("sans alt", sans_alt), ("sans dimensions (CLS)", sans_dim),
                       ("format ancien", anciennes)]:
        print(f"  {'🔴' if n else '🟢'} {libelle:<28} {n}")

    if total_ko:
        gain = int(total_ko * 0.45)  # conversion WebP + redimensionnement
        print(f"\n  Gain estimé en passant tout en WebP correctement dimensionné :")
        print(f"  environ {gain} Ko, soit {gain * 100 // max(total_ko, 1)} % du poids images.")

    if problemes:
        print(f"\n─── Détail ({len(problemes)} images à corriger) ───\n")
        for url_img, soucis in problemes[:15]:
            print(f"  {urlparse(url_img).path[-60:]}")
            for s in soucis:
                print(f"     • {s}")
            print()
        if len(problemes) > 15:
            print(f"  … et {len(problemes) - 15} autres, voir {args.exporter}\n")

    print(f"Détail complet dans {args.exporter}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
