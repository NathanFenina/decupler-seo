#!/usr/bin/env python3
"""Crawler SEO — explore un site et en sort l'inventaire complet.

    python3 scripts/crawl_site.py https://exemple.com --max 500
    python3 scripts/crawl_site.py https://exemple.com --exporter crawl.csv

Respecte robots.txt, limite le débit, reste sur le domaine de départ.
Sort un CSV exploitable par internal_pagerank.py et par les skills.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Dépendances manquantes. Lancez : pip install -r requirements.txt", file=sys.stderr)
    raise SystemExit(1)

AGENT = "ClaudeCodeSEODecupler/2.0 (+https://decupler.com)"

# Extensions qu'on ne crawle pas : ce ne sont pas des pages HTML.
EXTENSIONS_IGNOREES = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".svg", ".ico",
    ".zip", ".gz", ".mp4", ".mp3", ".woff", ".woff2", ".ttf", ".css", ".js",
    ".xml", ".json", ".doc", ".docx", ".xls", ".xlsx",
}


@dataclass
class Page:
    url: str
    statut: int = 0
    profondeur: int = 0
    title: str = ""
    longueur_title: int = 0
    meta_description: str = ""
    longueur_meta: int = 0
    h1: str = ""
    nb_h1: int = 0
    nb_h2: int = 0
    mots: int = 0
    canonical: str = ""
    indexable: bool = True
    raison_non_indexable: str = ""
    liens_sortants_internes: int = 0
    liens_sortants_externes: int = 0
    liens_entrants: int = 0
    temps_reponse_ms: int = 0
    poids_ko: int = 0
    a_schema: bool = False
    images_sans_alt: int = 0
    erreur: str = ""
    sources: list[str] = field(default_factory=list, repr=False)


def normaliser(url: str) -> str:
    """Retire le fragment et le slash final, pour ne pas crawler deux fois la même page."""
    url, _ = urldefrag(url)
    if url.endswith("/") and urlparse(url).path != "/":
        url = url[:-1]
    return url


def meme_domaine(url: str, hote: str) -> bool:
    return urlparse(url).netloc.lower().removeprefix("www.") == hote


def crawlable(url: str) -> bool:
    chemin = urlparse(url).path.lower()
    return not any(chemin.endswith(ext) for ext in EXTENSIONS_IGNOREES)


def analyser(html: str, url: str, hote: str) -> tuple[dict, list[str]]:
    """Extrait les signaux SEO d'une page et la liste de ses liens internes."""
    soup = BeautifulSoup(html, "html.parser")

    title = (soup.title.string or "").strip() if soup.title else ""
    meta_desc_tag = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    meta_desc = (meta_desc_tag.get("content") or "").strip() if meta_desc_tag else ""

    h1s = soup.find_all("h1")
    canonical_tag = soup.find("link", attrs={"rel": re.compile("^canonical$", re.I)})
    canonical = canonical_tag.get("href", "") if canonical_tag else ""

    # Indexabilité : on vérifie la meta robots ET la meta googlebot.
    indexable, raison = True, ""
    for nom in ("robots", "googlebot"):
        balise = soup.find("meta", attrs={"name": re.compile(f"^{nom}$", re.I)})
        if balise and "noindex" in (balise.get("content") or "").lower():
            indexable, raison = False, f"meta {nom} noindex"
            break

    # Le texte utile : on retire ce qui n'est pas du contenu lisible.
    for balise in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        balise.decompose()
    mots = len(soup.get_text(" ", strip=True).split())

    internes, externes = [], 0
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        absolue = normaliser(urljoin(url, href))
        if meme_domaine(absolue, hote):
            internes.append(absolue)
        else:
            externes += 1

    images = soup.find_all("img")
    sans_alt = sum(1 for img in images if not (img.get("alt") or "").strip())

    return (
        {
            "title": title,
            "longueur_title": len(title),
            "meta_description": meta_desc,
            "longueur_meta": len(meta_desc),
            "h1": h1s[0].get_text(strip=True)[:200] if h1s else "",
            "nb_h1": len(h1s),
            "nb_h2": len(soup.find_all("h2")),
            "mots": mots,
            "canonical": canonical,
            "indexable": indexable,
            "raison_non_indexable": raison,
            "liens_sortants_internes": len(set(internes)),
            "liens_sortants_externes": externes,
            "a_schema": bool(soup.find("script", attrs={"type": "application/ld+json"})),
            "images_sans_alt": sans_alt,
        },
        internes,
    )


def crawler(depart: str, maxi: int, delai_ms: int, respecter_robots: bool) -> dict[str, Page]:
    depart = normaliser(depart)
    hote = urlparse(depart).netloc.lower().removeprefix("www.")

    robots = RobotFileParser()
    if respecter_robots:
        robots.set_url(urljoin(depart, "/robots.txt"))
        try:
            robots.read()
        except Exception:
            # Un robots.txt illisible ne doit pas bloquer le crawl.
            robots = None
    else:
        robots = None

    session = requests.Session()
    session.headers["User-Agent"] = AGENT

    pages: dict[str, Page] = {}
    file = deque([(depart, 0)])
    vues = {depart}

    while file and len(pages) < maxi:
        url, profondeur = file.popleft()

        if robots and not robots.can_fetch(AGENT, url):
            continue

        page = Page(url=url, profondeur=profondeur)
        debut = time.monotonic()
        try:
            rep = session.get(url, timeout=30, allow_redirects=True)
            page.temps_reponse_ms = int((time.monotonic() - debut) * 1000)
            page.statut = rep.status_code
            page.poids_ko = len(rep.content) // 1024

            if rep.status_code == 200 and "text/html" in rep.headers.get("Content-Type", ""):
                # Le X-Robots-Tag en header est le noindex le plus souvent oublié.
                entete = rep.headers.get("X-Robots-Tag", "").lower()
                donnees, internes = analyser(rep.text, url, hote)
                if "noindex" in entete:
                    donnees["indexable"] = False
                    donnees["raison_non_indexable"] = "header X-Robots-Tag noindex"
                for cle, valeur in donnees.items():
                    setattr(page, cle, valeur)

                for lien in internes:
                    if lien in pages:
                        pages[lien].liens_entrants += 1
                    if lien not in vues and crawlable(lien) and len(vues) < maxi * 3:
                        vues.add(lien)
                        file.append((lien, profondeur + 1))
                    # On mémorise la source pour pouvoir compter les entrants
                    # des pages pas encore crawlées.
                    page.sources.append(lien)
        except requests.RequestException as exc:
            page.erreur = str(exc)[:200]

        pages[url] = page
        print(f"  [{len(pages):>4}/{maxi}] {page.statut} p{profondeur} {url}", file=sys.stderr)
        time.sleep(delai_ms / 1000)

    # Second passage : compter les liens entrants pour toutes les pages crawlées.
    for page in pages.values():
        page.liens_entrants = 0
    for page in pages.values():
        for cible in set(page.sources):
            if cible in pages and cible != page.url:
                pages[cible].liens_entrants += 1

    return pages


def resumer(pages: dict[str, Page]) -> None:
    total = len(pages)
    orphelines = [p for p in pages.values() if p.liens_entrants == 0 and p.profondeur > 0]
    erreurs = [p for p in pages.values() if p.statut >= 400 or p.erreur]
    redirs = [p for p in pages.values() if 300 <= p.statut < 400]
    non_index = [p for p in pages.values() if not p.indexable]
    minces = [p for p in pages.values() if 0 < p.mots < 300]
    profondes = [p for p in pages.values() if p.profondeur >= 4]
    sans_title = [p for p in pages.values() if p.statut == 200 and not p.title]
    multi_h1 = [p for p in pages.values() if p.nb_h1 > 1]

    print(f"\n{'═' * 60}")
    print(f"  {total} pages crawlées")
    print(f"{'═' * 60}")
    for libelle, lot in [
        ("erreurs (4xx/5xx)", erreurs),
        ("redirections", redirs),
        ("non indexables", non_index),
        ("orphelines", orphelines),
        ("contenu mince (<300 mots)", minces),
        ("profondeur ≥ 4", profondes),
        ("sans title", sans_title),
        ("H1 multiples", multi_h1),
    ]:
        marque = "🔴" if lot and libelle.startswith(("erreurs", "orphelines")) else ("🟠" if lot else "🟢")
        print(f"  {marque} {libelle:<28} {len(lot)}")
    print()


def main() -> int:
    p = argparse.ArgumentParser(description="Crawler SEO Décupler")
    p.add_argument("url")
    p.add_argument("--max", type=int, default=500, help="pages maximum (défaut 500)")
    p.add_argument("--delai", type=int, default=1000, help="délai entre requêtes en ms")
    p.add_argument("--exporter", default="crawl.csv", help="fichier CSV de sortie")
    p.add_argument("--ignorer-robots", action="store_true", help="ne pas respecter robots.txt")
    args = p.parse_args()

    print(f"Crawl de {args.url} — max {args.max} pages\n", file=sys.stderr)
    pages = crawler(args.url, args.max, args.delai, not args.ignorer_robots)

    champs = [c for c in asdict(next(iter(pages.values()))) if c != "sources"]
    with open(args.exporter, "w", newline="", encoding="utf-8") as f:
        ecrivain = csv.DictWriter(f, fieldnames=champs)
        ecrivain.writeheader()
        for page in pages.values():
            ligne = {c: getattr(page, c) for c in champs}
            ecrivain.writerow(ligne)

    resumer(pages)
    print(f"Inventaire écrit dans {args.exporter}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
