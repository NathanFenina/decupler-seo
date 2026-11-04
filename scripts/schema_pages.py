#!/usr/bin/env python3
"""Contrôle des données structurées servies par un site en production (skill seo-schema-jsonld).

Lit le JSON-LD du HTML servi des pages de memoire/cartographie.csv (ou des URL données) et signale :
  - JSON-LD invalide ;
  - trio sémantique absent : l'Organisation et la Personne du site doivent être définies sur chaque page ;
  - une deuxième Organisation ou Personne du même nom avec un autre @id ou sans @id ;
  - l'Organisation ou la Personne écrite en objet au lieu d'un @id (provider, author, publisher…) ;
  - un Service sans lien @id vers l'Organisation (provider ou parentOrganization) ;
  - un areaServed mal typé (un département, une région ou un pays déclaré en City, une ville en Country…) ;
  - plusieurs FAQPage sur une page, ou une question de FAQPage absente du texte visible ;
  - un @type inconnu de la liste (faute de frappe) ;
  - un sameAs connu comme mort (--sameas-mort) ; avec --verifier-liens,
    chaque sameAs est appelé (403, 429 et 999 = non vérifiable : LinkedIn et consorts bloquent les robots).

    python3 schema_pages.py --site https://exemple.fr --org-nom "Exemple" --personne-nom "Prénom Nom" \
        --limite 10 --sortie rapports/schema-pages-AAAA-MM.md
    python3 schema_pages.py --site https://exemple.fr --urls https://exemple.fr/page/ --verifier-liens

Par défaut : Organisation <site>/#organization, Personne <site>/#<personne-nom en slug>, URL lues dans
memoire/cartographie.csv du projet (colonnes url et statut ; pages programmées ignorées).

Lecture seule : aucune page n'est modifiée. Code de sortie 1 s'il y a au moins une erreur.
"""
import argparse
import csv
import html
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

CARTO = Path("memoire") / "cartographie.csv"
ORG = PERS = SITE = ""
NOMS_ORG, NOMS_PERS = set(), set()
UA = "Mozilla/5.0 (compatible; decupler-seo-controle-schema/1.0)"

# sameAs qu'on sait morts (--sameas-mort) : ne jamais les servir.
SAMEAS_MORTS = {}

# Zones qui ne sont pas des villes (areaServed) : départements et régions français (complétez au besoin).
DEPARTEMENTS = {"alpes-maritimes", "var", "bouches-du-rhône", "06", "83", "13", "gironde", "rhône", "nord",
                "hérault", "haute-garonne", "loire-atlantique", "ille-et-vilaine", "bas-rhin", "paris"}
REGIONS = {"provence-alpes-côte d'azur", "paca", "île-de-france", "hauts-de-france", "grand est", "bretagne",
           "pays de la loire", "auvergne-rhône-alpes", "occitanie", "nouvelle-aquitaine", "côte d'azur"}
PAYS = {"france", "belgique", "suisse", "luxembourg", "canada", "monaco"}

TYPES_CONNUS = {
    "WebPage", "WebSite", "ImageObject", "BreadcrumbList", "ListItem", "Organization", "Person", "FAQPage",
    "Question", "Answer", "Service", "ProfessionalService", "LocalBusiness", "Article", "BlogPosting",
    "NewsArticle", "TechArticle", "HowTo", "HowToStep", "Offer", "OfferCatalog", "AggregateRating", "Review",
    "Rating", "PostalAddress", "GeoCoordinates", "City", "Country", "AdministrativeArea", "Place", "State",
    "PropertyValue", "ContactPoint", "SearchAction", "EntryPoint", "ReadAction", "Thing", "DefinedTerm",
    "SoftwareApplication", "WebApplication", "VideoObject", "CollectionPage", "ItemList", "AboutPage",
    "ContactPage", "ProfilePage", "Event", "Course", "EducationalOrganization", "MonetaryAmount",
    "PriceSpecification", "UnitPriceSpecification", "OpeningHoursSpecification", "SiteNavigationElement",
    "CreativeWork", "Dataset", "Product", "Brand", "QuantitativeValue", "Language", "SpeakableSpecification",
    "WPHeader", "WPFooter", "Table", "Map", "MediaObject", "Occupation", "Corporation",
    "PropertyValueSpecification", "ServiceChannel",
}
REFS = ("provider", "author", "publisher", "parentOrganization", "founder", "worksFor", "creator", "brand",
        "sourceOrganization", "copyrightHolder", "reviewedBy", "editor")


def lire(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "replace")


def statut_lien(url, cache={}):
    if url in cache:
        return cache[url]
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
        with urllib.request.urlopen(req, timeout=20) as r:
            code = r.status
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception:
        code = 0
    cache[url] = code
    return code


def noeuds(blocs):
    """Aplatit les blocs JSON-LD en liste de nœuds (dictionnaires), récursivement."""
    sortie = []

    def visite(x):
        if isinstance(x, dict):
            if "@type" in x:
                sortie.append(x)
            for k, v in x.items():
                if k != "@context":
                    visite(v)
        elif isinstance(x, list):
            for v in x:
                visite(v)
    for b in blocs:
        visite(b)
    return sortie


def types(n):
    t = n.get("@type")
    return t if isinstance(t, list) else [t]


APOS = str.maketrans({"\u2019": "'", "\u2018": "'", "\u00a0": " ", "\u202f": " ", "\u2009": " "})


def texte_visible(page):
    corps = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", page, flags=re.S | re.I)
    corps = re.sub(r"<[^>]+>", " ", corps)
    return re.sub(r"\s+", " ", html.unescape(corps).translate(APOS)).lower()


def norm(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", str(s))).translate(APOS)
    return re.sub(r"\s+", " ", s).strip().lower()


def controle(url, page, verifier_liens=False):
    erreurs, alertes = [], []
    blocs = []
    for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', page, re.S | re.I):
        brut = m.group(1).strip()
        try:
            blocs.append(json.loads(brut))
        except json.JSONDecodeError as e:
            erreurs.append(f"JSON-LD invalide ({e.msg}, caractère {e.pos})")
    if not blocs:
        erreurs.append("aucun JSON-LD servi")
        return erreurs, alertes
    ns = noeuds(blocs)
    ids = {}
    for n in ns:
        if n.get("@id"):
            ids.setdefault(n["@id"], set()).update(t for t in types(n) if t)

    # Trio sémantique
    if ORG not in ids:
        erreurs.append(f"Organisation {ORG} absente")
    if PERS and PERS not in ids:
        alertes.append(f"Personne {PERS} absente")
    for n in ns:
        nom = norm(n.get("name", ""))
        ts = set(t for t in types(n) if t)
        if "Organization" in ts and nom in NOMS_ORG and n.get("@id") != ORG:
            erreurs.append(f"Organisation « {n.get('name')} » définie avec @id {n.get('@id') or 'absent'} au lieu de {ORG}")
        if "Person" in ts and nom in NOMS_PERS and n.get("@id") != PERS:
            erreurs.append(f"Personne « {n.get('name')} » définie avec @id {n.get('@id') or 'absent'} au lieu de {PERS}")
        for cle in REFS:
            v = n.get(cle)
            for x in (v if isinstance(v, list) else [v]):
                if isinstance(x, dict) and "@type" in x and not x.get("@id"):
                    nx = norm(x.get("name", ""))
                    if nx in NOMS_ORG | NOMS_PERS:
                        erreurs.append(f"{cle} de {'/'.join(map(str, types(n)))} : « {x.get('name')} » écrit en objet, sans @id")

    # Types inconnus
    for n in ns:
        for t in types(n):
            if t and t not in TYPES_CONNUS:
                alertes.append(f"@type inconnu : {t}")

    # Services : lien vers l'Organisation, areaServed bien typé
    for n in ns:
        ts = set(t for t in types(n) if t)
        if ts & {"Service", "ProfessionalService", "LocalBusiness"} and n.get("@id") != ORG:
            liens = [n.get("provider"), n.get("parentOrganization"), n.get("brand")]
            if not any(isinstance(x, dict) and x.get("@id") == ORG for x in liens):
                erreurs.append(f"{'/'.join(ts)} {n.get('@id') or ''} sans provider ni parentOrganization en @id {ORG}")
        zones = n.get("areaServed")
        for z in (zones if isinstance(zones, list) else [zones]):
            if not isinstance(z, dict):
                continue
            nom, tz = norm(z.get("name", "")), z.get("@type")
            if tz == "City" and (nom in DEPARTEMENTS or nom in REGIONS or nom in PAYS):
                erreurs.append(f"areaServed « {z.get('name')} » déclaré City : c'est une zone administrative ou un pays")
            if tz == "Country" and nom not in PAYS:
                alertes.append(f"areaServed « {z.get('name')} » déclaré Country")
        nom_n = str(n.get("name", ""))
        if re.search(r"\bà (Var|Alpes-Maritimes|Bouches-du-Rhône)\b", nom_n):
            alertes.append(f"nom d'entité « {nom_n} » : « dans le », pas « à »")

    # FAQPage
    faqs = [n for n in ns if "FAQPage" in types(n)]
    if len(faqs) > 1:
        erreurs.append(f"{len(faqs)} FAQPage sur la page (une seule attendue)")
    visible = texte_visible(page)
    for f in faqs:
        qs = f.get("mainEntity") or []
        for q in (qs if isinstance(qs, list) else [qs]):
            if not isinstance(q, dict):
                continue
            nom = norm(q.get("name", ""))
            cle = nom[:55].rstrip(" ?")
            if cle and cle not in visible:
                erreurs.append(f"question de FAQPage absente du texte visible : « {q.get('name', '')[:80]} »")

    # sameAs
    vus = set()
    for n in ns:
        sa = n.get("sameAs")
        for s in (sa if isinstance(sa, list) else [sa]):
            if not isinstance(s, str) or s in vus:
                continue
            vus.add(s)
            if s in SAMEAS_MORTS:
                erreurs.append(f"sameAs mort : {s} ({SAMEAS_MORTS[s]})")
            elif verifier_liens:
                code = statut_lien(s)
                if code in (403, 429, 999):
                    pass
                elif code == 0 or code >= 400:
                    erreurs.append(f"sameAs injoignable : {s} (HTTP {code or 'erreur réseau'})")
    return erreurs, alertes


def urls_cartographie():
    with CARTO.open(encoding="utf-8") as f:
        for ligne in csv.DictReader(f):
            u = (ligne.get("url") or "").strip()
            st = (ligne.get("statut") or "").lower()
            if u.startswith(SITE) and ("programm" not in st and "à publier" not in st):
                yield u


def main():
    global ORG, PERS, SITE
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True, help="https://exemple.fr")
    ap.add_argument("--org-nom", action="append", default=[], help="nom de l'Organisation (répétable)")
    ap.add_argument("--personne-nom", action="append", default=[], help="nom de la Personne (répétable)")
    ap.add_argument("--org-id"); ap.add_argument("--personne-id")
    ap.add_argument("--sameas-mort", action="append", default=[], help="URL de sameAs à ne plus servir (répétable)")
    ap.add_argument("--urls", nargs="*")
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--verifier-liens", action="store_true", help="appelle chaque sameAs (lent)")
    ap.add_argument("--sortie", help="rapport Markdown")
    a = ap.parse_args()
    SITE = a.site.rstrip("/") + "/"
    NOMS_ORG.update(norm(x) for x in a.org_nom)
    NOMS_PERS.update(norm(x) for x in a.personne_nom)
    ORG = a.org_id or SITE + "#organization"
    slug = re.sub(r"[^a-z0-9]+", "-", (a.personne_nom[0] if a.personne_nom else "").lower()).strip("-")
    PERS = a.personne_id or (SITE + "#" + slug if slug else "")
    SAMEAS_MORTS.update({u: "déclaré mort (--sameas-mort)" for u in a.sameas_mort})
    urls = a.urls or list(dict.fromkeys(urls_cartographie()))
    if a.limite:
        urls = urls[:a.limite]
    lignes, total_e, total_a = [], 0, 0
    for u in urls:
        try:
            code, page = lire(u)
        except urllib.error.HTTPError as e:
            lignes.append((u, [f"HTTP {e.code}"], []))
            total_e += 1
            continue
        except Exception as e:
            lignes.append((u, [f"lecture impossible : {e}"], []))
            total_e += 1
            continue
        e, al = controle(u, page, a.verifier_liens)
        al = list(dict.fromkeys(al))
        total_e += len(e)
        total_a += len(al)
        lignes.append((u, e, al))
        etat = "OK" if not e and not al else f"{len(e)} erreur(s), {len(al)} alerte(s)"
        print(f"{etat:24} {u}")
        for x in e:
            print(f"    ✗ {x}")
        for x in al:
            print(f"    ! {x}")
    print(f"\n{len(urls)} page(s) : {total_e} erreur(s), {total_a} alerte(s).")
    if a.sortie:
        out = [f"# Contrôle des données structurées ({len(urls)} pages)", "",
               "Script : `schema_pages.py` (skill `seo-schema-jsonld`).", "",
               f"Total : {total_e} erreur(s), {total_a} alerte(s).", "",
               "| Page | Erreurs | Alertes |", "|---|---|---|"]
        for u, e, al in lignes:
            out.append(f"| {u.replace(SITE.rstrip('/'), '')} | {'<br>'.join(e) or 'aucune'} | {'<br>'.join(al) or 'aucune'} |")
        Path(a.sortie).write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"Rapport : {a.sortie}")
    sys.exit(1 if total_e else 0)


if __name__ == "__main__":
    main()
