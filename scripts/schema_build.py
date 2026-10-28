#!/usr/bin/env python3
"""Génère le JSON-LD complet d'une page — un seul @graph, socle compris — puis le valide.

    python3 scripts/schema_build.py page.json --socle socle-global.json [--entites memoire/entites.csv] \\
        [--html] [--sortie page.jsonld]

Le fichier de page décrit ce qui est propre à l'URL ; le socle (Organization,
WebSite, logo) vient d'un seul fichier, identique sur tout le site. Les
entités de about / mentions se résolvent par leur nom dans le registre du
projet (memoire/entites.csv : QID et sameAs), jamais saisies à la main.

Exemple de page.json :

    {"url": "https://exemple.com/plombier-lyon/", "type": "service", "langue": "fr-FR",
     "titre": "Plombier à Lyon", "description": "Dépannage en 2 h…",
     "fil": [["Accueil", "https://exemple.com/"], ["Plombier à Lyon", "https://exemple.com/plombier-lyon/"]],
     "about": ["Plomberie"], "mentions": ["Chauffe-eau"],
     "service": {"nom": "Dépannage plomberie", "type": "Plomberie", "zone": "Lyon"},
     "faq": [["Combien coûte un dépannage ?", "Le devis est gratuit…"]]}

Types de page : accueil, page, service, article, contact, apropos, auteur.
Un article ajoute "article": {"titre", "publie", "modifie", "auteur": {"nom", "url"}, "image"} (image obligatoire) ;
about et mentions vont alors sur le BlogPosting, pas sur la WebPage.

Refuse : plus de 3 about, plus de 12 mentions, une entité dans les deux,
un article sans date ni auteur, un fil d'Ariane qui ne commence pas par
l'accueil. Sortie validée par schema_validate.py : une erreur → code 1.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import schema_validate as V  # noqa: E402
import triplets as T  # noqa: E402

TYPES_PAGE = {"accueil": "WebPage", "page": "WebPage", "service": "WebPage", "article": "WebPage",
              "contact": "ContactPage", "apropos": "AboutPage", "auteur": "ProfilePage"}
MAX_ABOUT, MAX_MENTIONS = 3, 12


class ErreurConfig(ValueError):
    pass


def racine(url: str) -> str:
    u = urlparse(url)
    return f"{u.scheme}://{u.netloc}/"


def id_socle(socle: list[dict], type_: str) -> str | None:
    return next((n.get("@id") for n in socle if type_ in V.types_de(n)), None)


def entites_noeuds(noms: list[str], registre: list[dict], role: str, avis: list[str]) -> list[dict]:
    res = []
    for nom in noms:
        e = T.trouver(nom, registre)
        if e is None:
            avis.append(f"{role} « {nom} » absent du registre : posé sans sameAs (à vérifier avant d'ajouter un QID)")
            e = {"entite": nom, "type": "Thing", "qid": "", "sameAs": []}
        res.append(T.noeud_entite(e))
    return res


def construire(page: dict, socle: list[dict], registre: list[dict] | None = None) -> tuple[dict, list[str]]:
    registre, avis = registre or [], []
    url = page.get("url") or ""
    if not url.startswith("https://"):
        raise ErreurConfig("url absente ou pas en https")
    type_page = page.get("type", "page")
    if type_page not in TYPES_PAGE:
        raise ErreurConfig(f"type « {type_page} » inconnu ({', '.join(TYPES_PAGE)})")
    about, mentions = list(page.get("about") or []), list(page.get("mentions") or [])
    if len(about) > MAX_ABOUT:
        raise ErreurConfig(f"{len(about)} entités en about : {MAX_ABOUT} au plus")
    if len(mentions) > MAX_MENTIONS:
        raise ErreurConfig(f"{len(mentions)} entités en mentions : {MAX_MENTIONS} au plus")
    doublons = {T.norm(x) for x in about} & {T.norm(x) for x in mentions}
    if doublons:
        raise ErreurConfig(f"entité à la fois en about et en mentions : {', '.join(sorted(doublons))}")

    org, site = id_socle(socle, "Organization"), id_socle(socle, "WebSite")
    if not org or not site:
        raise ErreurConfig("le socle doit contenir une Organization et un WebSite avec leur @id")
    base = url.split("#")[0]
    graphe = [*socle]
    page_noeud = {"@type": TYPES_PAGE[type_page], "@id": f"{base}#webpage", "url": base,
                  "name": page.get("titre") or "", "isPartOf": {"@id": site},
                  "inLanguage": page.get("langue") or "fr-FR"}
    if page.get("description"):
        page_noeud["description"] = page["description"]
    if type_page == "accueil":
        page_noeud["about"] = {"@id": org}
    graphe.append(page_noeud)

    porteur = page_noeud
    if type_page == "article":
        art = page.get("article") or {}
        auteur = art.get("auteur") or {}
        if not art.get("publie") or not auteur.get("nom") or not art.get("image"):
            raise ErreurConfig("un article demande article.publie, article.auteur.nom et article.image "
                               "(image requise par Google pour le résultat enrichi)")
        personne = {"@type": "Person", "@id": f"{auteur.get('url') or racine(url)}#person"
                    if auteur.get("url") else f"{racine(url)}#auteur-{T.norm(auteur['nom']).replace(' ', '-')}",
                    "name": auteur["nom"], "worksFor": {"@id": org}}
        if auteur.get("url"):
            personne["url"] = auteur["url"]
        if auteur.get("sameAs"):
            personne["sameAs"] = auteur["sameAs"]
        billet = {"@type": "BlogPosting", "@id": f"{base}#article",
                  "headline": (art.get("titre") or page.get("titre") or "")[:110],
                  "datePublished": art["publie"], "dateModified": art.get("modifie") or art["publie"],
                  "author": {"@id": personne["@id"]}, "publisher": {"@id": org},
                  "mainEntityOfPage": {"@id": page_noeud["@id"]}, "inLanguage": page_noeud["inLanguage"]}
        if art.get("image"):
            billet["image"] = art["image"]
        graphe += [personne, billet]
        page_noeud["mainEntity"] = {"@id": billet["@id"]}
        porteur = billet
    if about:
        noeuds = entites_noeuds(about, registre, "about", avis)
        porteur["about"] = noeuds if len(noeuds) > 1 else noeuds[0]
    if mentions:
        porteur["mentions"] = entites_noeuds(mentions, registre, "mentions", avis)

    if type_page == "service":
        s = page.get("service") or {}
        if not s.get("nom"):
            raise ErreurConfig("une page service demande service.nom")
        service = {"@type": "Service", "@id": f"{base}#service", "name": s["nom"],
                   "serviceType": s.get("type") or s["nom"], "provider": {"@id": org}}
        if s.get("zone"):
            service["areaServed"] = {"@type": "City", "name": s["zone"]}
        if s.get("categorie"):
            service["category"] = entites_noeuds([s["categorie"]], registre, "category", avis)[0]
        graphe.append(service)
        page_noeud["mainEntity"] = {"@id": service["@id"]}

    fil = page.get("fil") or []
    if fil:
        if urlparse(fil[0][1]).path not in ("", "/"):
            raise ErreurConfig("le fil d'Ariane commence par l'accueil")
        graphe.append({"@type": "BreadcrumbList", "@id": f"{base}#breadcrumb", "itemListElement": [
            {"@type": "ListItem", "position": i, "name": nom, "item": lien} for i, (nom, lien) in enumerate(fil, 1)]})
        page_noeud["breadcrumb"] = {"@id": f"{base}#breadcrumb"}

    faq = page.get("faq") or []
    if faq:
        if any(not (q or "").strip() or not (r or "").strip() for q, r in faq):
            raise ErreurConfig("une question ou une réponse de FAQ est vide")
        graphe.append({"@type": "FAQPage", "@id": f"{base}#faq", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}} for q, r in faq]})
        page_noeud.setdefault("hasPart", {"@id": f"{base}#faq"})

    return {"@context": "https://schema.org", "@graph": graphe}, avis


def valider(doc: dict) -> list[dict]:
    paires = list(V.parcourir(doc))
    return V.valider([n for n, _ in paires], [doc], [c for _, c in paires])


def main() -> int:
    p = argparse.ArgumentParser(description="Génère et valide le JSON-LD d'une page")
    p.add_argument("page", help="fichier JSON de la page")
    p.add_argument("--socle", required=True, help="socle-global.json (Organization, WebSite, logo)")
    p.add_argument("--entites", default="memoire/entites.csv", help="registre des entités du projet")
    p.add_argument("--html", action="store_true", help="sortie prête à coller dans <head>")
    p.add_argument("--sortie", help="écrire dans ce fichier plutôt que sur la sortie standard")
    a = p.parse_args()
    socle = json.loads(Path(a.socle).read_text(encoding="utf-8"))
    socle = socle.get("@graph", socle) if isinstance(socle, dict) else socle
    try:
        doc, avis = construire(json.loads(Path(a.page).read_text(encoding="utf-8")), socle,
                               T.charger_entites(a.entites))
    except ErreurConfig as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 1
    for x in avis:
        print(f"  ! {x}", file=sys.stderr)
    constats = valider(doc)
    for c in constats:
        print(f"  {'✗' if c['gravite'] == 'erreur' else '!'} {c['type']} : {c['message']}", file=sys.stderr)
    texte = json.dumps(doc, ensure_ascii=False, indent=2)
    if a.html:
        texte = f'<script type="application/ld+json">\n{texte}\n</script>'
    if a.sortie:
        Path(a.sortie).write_text(texte + "\n", encoding="utf-8")
    else:
        print(texte)
    return 1 if any(c["gravite"] == "erreur" for c in constats) else 0


if __name__ == "__main__":
    sys.exit(main())
