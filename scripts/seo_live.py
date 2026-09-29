#!/usr/bin/env python3
"""Santé SEO d'un site en production, et notification IndexNow.

    python3 seo_live.py                        # site de GSC_SITE_URL ou de la config
    python3 seo_live.py --site https://www.exemple.com --max 200
    python3 seo_live.py --ping                 # puis soumet les URL à IndexNow

Échoue (code 1) si : robots.txt est absent, bloque tout le site ou ne déclare
pas le sitemap ; une URL du sitemap ne répond pas 200 sans redirection, n'est
pas en https, porte un noindex, ou a une canonical qui ne pointe pas sur elle.

IndexNow prévient Bing, Yandex, Seznam, Naver et Yep — et Bing alimente la
recherche de ChatGPT et Copilot. Google ne l'utilise pas : pour Google, le
sitemap déclaré dans Search Console suffit. La clé (INDEXNOW_KEY) doit être
publiée à la racine du site, dans <clé>.txt : le script le vérifie avant
d'envoyer quoi que ce soit.

Sans dépendance. Poli : requêtes séquentielles, délai configurable.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import charger_env, lire_valeur  # noqa: E402

AGENT = "DecuplerSEO-LiveCheck/3.1 (+https://github.com/NathanFenina/decupler-seo)"
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


class SansRedirection(urllib.request.HTTPRedirectHandler):
    """Une redirection sur une URL du sitemap est un défaut à signaler, pas à suivre."""
    def redirect_request(self, *args, **kwargs):
        return None


OUVREUR = urllib.request.build_opener(SansRedirection)


def _get_une_fois(url: str, timeout: int) -> tuple[int, dict, str]:
    requete = urllib.request.Request(url, headers={"User-Agent": AGENT})
    try:
        with OUVREUR.open(requete, timeout=timeout) as rep:
            return rep.status, dict(rep.headers), rep.read(3_000_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers or {}), ""
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
        return 0, {}, str(exc)


def get(url: str, timeout: int = 30) -> tuple[int, dict, str]:
    """Une coupure réseau ou un 5xx se retente deux fois (2 s puis 6 s) avant d'être signalé.

    Constaté en test sur un site réel : deux pages « injoignables » au premier
    passage répondaient 200 en 1,5 s juste après. Un contrôle qui crie au loup
    finit ignoré, et c'est alors la vraie panne qu'on rate.
    """
    code, entetes, corps = _get_une_fois(url, timeout)
    for attente in (2, 6):
        if code != 0 and code < 500:
            break
        time.sleep(attente)
        code, entetes, corps = _get_une_fois(url, timeout)
    return code, entetes, corps


def normaliser(url: str) -> str:
    return url.split("#")[0].rstrip("/")


def urls_du_sitemap(url: str, maxi: int, vus: set[str] | None = None) -> list[str]:
    """Suit les index de sitemaps, sans boucler."""
    vus = vus or set()
    if url in vus:
        return []
    vus.add(url)
    statut, _, corps = get(url)
    if statut != 200 or not corps.strip():
        return []
    try:
        racine = ElementTree.fromstring(corps.encode("utf-8"))
    except ElementTree.ParseError:
        return []
    if racine.tag.endswith("sitemapindex"):
        urls: list[str] = []
        for loc in racine.findall("sm:sitemap/sm:loc", NS):
            urls += urls_du_sitemap(loc.text.strip(), maxi - len(urls), vus)
            if len(urls) >= maxi:
                break
        return urls[:maxi]
    return [loc.text.strip() for loc in racine.findall("sm:url/sm:loc", NS)][:maxi]


def site_par_defaut() -> str:
    site = os.environ.get("SEO_SITE", "") or os.environ.get("GSC_SITE_URL", "") or lire_valeur("projet.domaine")
    if not site or site.startswith("sc-domain:"):
        raise SystemExit("✗ Site inconnu : passez --site https://www.exemple.com")
    return site.rstrip("/")


def main() -> int:
    charger_env()
    ap = argparse.ArgumentParser(description="Santé SEO en production + IndexNow")
    ap.add_argument("--site")
    ap.add_argument("--max", type=int, default=500, help="URL du sitemap à contrôler")
    ap.add_argument("--delai", type=float, default=0.3, help="secondes entre deux requêtes")
    ap.add_argument("--ping", action="store_true", help="soumettre les URL à IndexNow")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    site = (a.site or site_par_defaut()).rstrip("/")
    erreurs: list[str] = []
    avertissements: list[str] = []

    # robots.txt
    statut, _, robots = get(f"{site}/robots.txt")
    if statut != 200:
        erreurs.append(f"robots.txt : HTTP {statut}")
    else:
        blocs = re.split(r"(?im)^user-agent:", robots)
        for bloc in blocs:
            if re.match(r"\s*\*\s*$", bloc.splitlines()[0] if bloc.splitlines() else "") and \
               re.search(r"(?im)^disallow:\s*/\s*$", bloc):
                erreurs.append("robots.txt bloque tout le site pour tous les robots (Disallow: /)")
    sitemaps = re.findall(r"(?im)^sitemap:\s*(\S+)", robots)
    if statut == 200 and not sitemaps:
        erreurs.append("robots.txt ne déclare aucun sitemap")
    sitemap = sitemaps[0] if sitemaps else f"{site}/sitemap.xml"

    # URL du sitemap
    urls = urls_du_sitemap(sitemap, a.max)
    if not urls:
        erreurs.append(f"sitemap vide ou illisible : {sitemap}")

    for url in urls:
        time.sleep(a.delai)
        code, entetes, html = get(url)
        chemin = urllib.parse.urlparse(url).path or "/"
        if code in (301, 302, 303, 307, 308):
            erreurs.append(f"{chemin} : redirection {code} vers {entetes.get('Location', '?')} — "
                           "le sitemap doit lister l'URL finale")
            continue
        if code != 200:
            erreurs.append(f"{chemin} : HTTP {code or 'injoignable'}")
            continue
        if not url.startswith("https://"):
            erreurs.append(f"{chemin} : pas en https")
        robots_entete = entetes.get("X-Robots-Tag", "") or entetes.get("x-robots-tag", "")
        meta_robots = re.search(r'<meta[^>]+name=["\']robots["\'][^>]*content=["\']([^"\']*)', html, re.I)
        if "noindex" in robots_entete.lower() or (meta_robots and "noindex" in meta_robots.group(1).lower()):
            erreurs.append(f"{chemin} : noindex alors que la page est dans le sitemap")
        canon = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', html, re.I) or \
            re.search(r'<link[^>]+href=["\']([^"\']+)["\'][^>]*rel=["\']canonical', html, re.I)
        if not canon:
            avertissements.append(f"{chemin} : aucune canonical")
        elif normaliser(urllib.parse.urljoin(url, canon.group(1))) != normaliser(url):
            erreurs.append(f"{chemin} : canonical vers {canon.group(1)}")

    # IndexNow
    ping = None
    if a.ping and urls:
        cle = os.environ.get("INDEXNOW_KEY", "").strip()
        if not cle:
            erreurs.append("--ping demandé mais INDEXNOW_KEY absente")
        else:
            code_cle, _, contenu_cle = get(f"{site}/{cle}.txt")
            if code_cle != 200 or contenu_cle.strip() != cle:
                erreurs.append(f"IndexNow : {site}/{cle}.txt absent ou incorrect — publiez-le avant de pinguer")
            else:
                corps = json.dumps({"host": urllib.parse.urlparse(site).netloc, "key": cle,
                                    "keyLocation": f"{site}/{cle}.txt", "urlList": urls[:10000]}).encode()
                requete = urllib.request.Request("https://api.indexnow.org/indexnow", data=corps, method="POST",
                                                 headers={"Content-Type": "application/json; charset=utf-8",
                                                          "User-Agent": AGENT})
                try:
                    with urllib.request.urlopen(requete, timeout=60) as rep:
                        ping = rep.status
                except urllib.error.HTTPError as exc:
                    ping = exc.code
                    if exc.code not in (200, 202):
                        erreurs.append(f"IndexNow : HTTP {exc.code}")

    if a.json:
        print(json.dumps({"site": site, "sitemap": sitemap, "urls": len(urls), "erreurs": erreurs,
                          "avertissements": avertissements, "indexnow": ping}, ensure_ascii=False, indent=1))
    else:
        print(f"\n  {site} · sitemap {sitemap} · {len(urls)} URL contrôlée(s)\n")
        for e in erreurs:
            print(f"  ✗ {e}")
        for w in avertissements[:20]:
            print(f"  ! {w}")
        if ping:
            print(f"  → IndexNow : {len(urls)} URL soumises (HTTP {ping})")
        print("\n  " + ("✗ Problèmes à corriger." if erreurs else "✓ Tout est sain.") + "\n")
    return 1 if erreurs else 0


if __name__ == "__main__":
    sys.exit(main())
