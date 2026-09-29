#!/usr/bin/env python3
"""Récupère une page web et en extrait les signaux SEO.

    python3 scripts/fetch_page.py https://exemple.com
    python3 scripts/fetch_page.py https://exemple.com --json
    python3 scripts/fetch_page.py https://exemple.com --html sortie.html

Sert de brique de base aux skills qui ont besoin de lire une page sans
passer par un MCP : audit, on-page, schema, images.

Refuse les adresses internes (SSRF) : un skill qui reçoit une URL depuis
un fichier, une SERP ou un contenu tiers ne doit pas pouvoir servir de
relais vers le réseau local ou vers les métadonnées d'instance cloud.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Dépendances manquantes. Lancez : pip install -r requirements.txt", file=sys.stderr)
    raise SystemExit(1)

AGENT = "ClaudeCodeSEODecupler/2.0 (+https://decupler.com)"
TAILLE_MAX = 10 * 1024 * 1024  # 10 Mo : au-delà, ce n'est plus une page web


def verifier_url(url: str) -> str:
    """Valide l'URL et refuse tout ce qui pointe vers le réseau interne.

    Chaque adresse résolue est contrôlée, pas seulement la première : un
    nom de domaine peut résoudre vers plusieurs IP dont une seule est
    privée. La résolution est faite ici, mais requests la refera de son
    côté — une réattribution DNS entre les deux reste théoriquement
    possible. Pour un usage SEO ce niveau de garantie suffit ; ne vous en
    servez pas comme d'un proxy de sécurité.
    """
    decoupee = urlparse(url)

    if decoupee.scheme not in ("http", "https"):
        raise ValueError(f"Schéma « {decoupee.scheme or '(vide)'} » refusé. Utilisez http ou https.")
    if not decoupee.netloc:
        raise ValueError("URL sans nom de domaine.")

    hote = decoupee.hostname or ""
    try:
        infos = socket.getaddrinfo(hote, None)
    except socket.gaierror as exc:
        raise ValueError(f"Domaine « {hote} » introuvable : {exc}") from exc

    for info in infos:
        adresse = ipaddress.ip_address(info[4][0])
        if (adresse.is_private or adresse.is_loopback or adresse.is_link_local
                or adresse.is_reserved or adresse.is_multicast):
            raise ValueError(
                f"« {hote} » résout vers une adresse interne ({adresse}). "
                "Refusé : ce script ne sert pas de relais vers le réseau local."
            )
    return url


def extraire(html: str, url: str, entetes: dict, statut: int) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    def meta(nom: str, attribut: str = "name") -> str:
        balise = soup.find("meta", attrs={attribut: re.compile(f"^{nom}$", re.I)})
        return (balise.get("content") or "").strip() if balise else ""

    # Indexabilité : la meta robots, la meta googlebot et le header
    # X-Robots-Tag peuvent chacun poser un noindex. Le header est celui
    # qu'on oublie, parce qu'il n'apparaît pas dans le HTML.
    directives = [meta("robots").lower(), meta("googlebot").lower(),
                  entetes.get("X-Robots-Tag", "").lower()]
    noindex = any("noindex" in d for d in directives)
    nofollow = any("nofollow" in d for d in directives)

    canonical = soup.find("link", attrs={"rel": re.compile("^canonical$", re.I)})

    titres = {}
    for niveau in range(1, 7):
        trouves = [t.get_text(strip=True) for t in soup.find_all(f"h{niveau}")]
        if trouves:
            titres[f"h{niveau}"] = trouves

    jsonld = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            jsonld.append(json.loads(script.get_text()))
        except json.JSONDecodeError:
            jsonld.append({"_erreur": "JSON invalide — ce bloc est ignoré par Google"})

    images = soup.find_all("img")
    liens = soup.find_all("a", href=True)
    hote = urlparse(url).netloc.lower().removeprefix("www.")

    def est_interne(href: str) -> bool:
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            return False
        if not href.startswith("http"):
            return True
        return urlparse(href).netloc.lower().removeprefix("www.") == hote

    # Le texte utile : on écarte ce qui n'est pas du contenu lisible.
    copie = BeautifulSoup(html, "html.parser")
    for balise in copie(["script", "style", "nav", "footer", "header", "noscript"]):
        balise.decompose()
    texte = copie.get_text(" ", strip=True)

    return {
        "url": url,
        "statut": statut,
        "title": (soup.title.string or "").strip() if soup.title else "",
        "meta_description": meta("description"),
        "canonical": canonical.get("href", "") if canonical else "",
        "lang": (soup.html.get("lang", "") if soup.html else ""),
        "indexable": not noindex,
        "nofollow": nofollow,
        "directives_robots": [d for d in directives if d],
        "titres": titres,
        "mots": len(texte.split()),
        "texte": texte,
        "jsonld": jsonld,
        "og": {c: meta(f"og:{c}", "property") for c in ("title", "description", "image", "type")},
        "hreflang": [
            {"code": l.get("hreflang"), "href": l.get("href")}
            for l in soup.find_all("link", attrs={"rel": re.compile("^alternate$", re.I)})
            if l.get("hreflang")
        ],
        "images": {
            "total": len(images),
            "sans_alt": sum(1 for i in images if not (i.get("alt") or "").strip()),
            "sans_dimensions": sum(1 for i in images if not (i.get("width") and i.get("height"))),
        },
        "liens": {
            "internes": sum(1 for a in liens if est_interne(a["href"])),
            "externes": sum(1 for a in liens if not est_interne(a["href"])
                            and a["href"].startswith("http")),
        },
        "entetes": {c: entetes.get(c, "") for c in
                    ("Content-Type", "X-Robots-Tag", "Strict-Transport-Security", "Server")},
    }


def recuperer(url: str) -> tuple[dict, str]:
    verifier_url(url)
    session = requests.Session()
    session.max_redirects = 5
    reponse = session.get(url, headers={"User-Agent": AGENT}, timeout=30, stream=True)

    # Chaque étape d'une redirection peut sortir du périmètre autorisé.
    for etape in reponse.history:
        verifier_url(etape.url)
    verifier_url(reponse.url)

    contenu = b""
    for morceau in reponse.iter_content(8192):
        contenu += morceau
        if len(contenu) > TAILLE_MAX:
            raise ValueError(f"Page au-delà de {TAILLE_MAX // 1024 // 1024} Mo — interrompue.")

    html = contenu.decode(reponse.encoding or "utf-8", errors="replace")
    donnees = extraire(html, reponse.url, dict(reponse.headers), reponse.status_code)
    donnees["redirections"] = [{"de": e.url, "statut": e.status_code} for e in reponse.history]
    donnees["poids_ko"] = len(contenu) // 1024
    return donnees, html


def afficher(d: dict) -> None:
    print(f"\n{'═' * 62}")
    print(f"  {d['url']}")
    print(f"  HTTP {d['statut']} · {d['poids_ko']} Ko · {d['mots']} mots")
    print(f"{'═' * 62}\n")

    if d["redirections"]:
        print(f"  Redirections : {len(d['redirections'])} saut(s)")
        for r in d["redirections"]:
            print(f"    {r['statut']} ← {r['de']}")
        print()

    if not d["indexable"]:
        print(f"  🔴 NON INDEXABLE — {', '.join(d['directives_robots'])}\n")

    title = d["title"]
    print(f"  Title      ({len(title)} car.) {title or '— absent'}")
    meta = d["meta_description"]
    print(f"  Meta desc. ({len(meta)} car.) {meta[:70] or '— absente'}")
    print(f"  Canonical  {d['canonical'] or '— absente'}")
    print(f"  Langue     {d['lang'] or '— non déclarée'}")

    h1 = d["titres"].get("h1", [])
    marque = "🔴" if len(h1) != 1 else "  "
    print(f"  {marque}H1        {len(h1)} — {h1[0][:60] if h1 else '(aucun)'}")
    print(f"    H2        {len(d['titres'].get('h2', []))}")

    print(f"\n  Images     {d['images']['total']} · "
          f"{d['images']['sans_alt']} sans alt · "
          f"{d['images']['sans_dimensions']} sans dimensions")
    print(f"  Liens      {d['liens']['internes']} internes · {d['liens']['externes']} externes")
    print(f"  JSON-LD    {len(d['jsonld'])} bloc(s)")
    if d["hreflang"]:
        print(f"  Hreflang   {len(d['hreflang'])} alternative(s)")
    print()


def main() -> int:
    p = argparse.ArgumentParser(description="Récupération et extraction SEO d'une page")
    p.add_argument("url")
    p.add_argument("--json", action="store_true", help="sortie JSON complète")
    p.add_argument("--html", metavar="FICHIER", help="enregistre le HTML brut")
    p.add_argument("--texte", action="store_true", help="affiche le texte extrait")
    args = p.parse_args()

    try:
        donnees, html = recuperer(args.url)
    except ValueError as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 2
    except requests.RequestException as exc:
        print(f"✗ Requête échouée : {exc}", file=sys.stderr)
        return 1

    if args.html:
        Path(args.html).write_text(html, encoding="utf-8")
        print(f"HTML enregistré dans {args.html}", file=sys.stderr)

    if args.json:
        print(json.dumps(donnees, ensure_ascii=False, indent=2))
    elif args.texte:
        print(donnees["texte"])
    else:
        afficher(donnees)
    return 0


if __name__ == "__main__":
    sys.exit(main())
