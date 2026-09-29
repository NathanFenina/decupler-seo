#!/usr/bin/env python3
"""Validation des données structurées JSON-LD.

    python3 scripts/schema_validate.py https://exemple.com/page
    python3 scripts/schema_validate.py page.html --socle socle-global.json
    python3 scripts/schema_validate.py fichier.jsonld --json
    python3 scripts/schema_validate.py page.html --strict      # code 1 sur erreur

Trois niveaux : JSON valide, conformité schema.org, exigences Google.
Plus les règles de la méthode : un seul script JSON-LD par page, @id uniques
et références résolues dans le graphe, socle global identique au fichier de
référence, URL absolues, dates ISO 8601, aucun texte provisoire (A_CONFIRMER),
sameAs Wikidata/Wikipédia bien formés, pièges connus (SoftwareApplication
pour un logiciel simplement cité, SearchAction, note auto-attribuée…).

Sans dépendance pour un fichier local (.jsonld, .json ou .html) ;
requests pour une URL.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

# Propriétés exigées par Google pour obtenir le rich result.
# Plus strictes que schema.org : un schema valide côté vocabulaire peut
# n'afficher aucun rich result s'il manque une de ces propriétés.
REQUISES_GOOGLE = {
    "Article": ["headline", "image", "datePublished", "author"],
    "NewsArticle": ["headline", "image", "datePublished", "author"],
    "BlogPosting": ["headline", "image", "datePublished", "author"],
    "Product": ["name", "image", "offers"],
    "Offer": ["price", "priceCurrency", "availability"],
    "LocalBusiness": ["name", "address", "telephone"],
    "Organization": ["name", "url"],
    "Person": ["name"],
    "BreadcrumbList": ["itemListElement"],
    "ListItem": ["position"],
    "FAQPage": ["mainEntity"],
    "Question": ["name", "acceptedAnswer"],
    "Answer": ["text"],
    "VideoObject": ["name", "description", "thumbnailUrl", "uploadDate"],
    "Event": ["name", "startDate", "location"],
    "Recipe": ["name", "image", "recipeIngredient", "recipeInstructions"],
    "JobPosting": ["title", "description", "datePosted", "hiringOrganization"],
    "Course": ["name", "description", "provider"],
    "SoftwareApplication": ["name", "applicationCategory", "offers"],
}

# Propriétés que la méthode attend en plus : pas de rich result en jeu, mais
# sans elles le graphe ne relie pas la page à l'entité (signalé, non bloquant).
ATTENDUES_METHODE = {
    "WebSite": ["name", "url", "publisher"],
    "WebPage": ["url", "name", "isPartOf"],
    "CollectionPage": ["url", "name", "isPartOf"],
    "AboutPage": ["url", "name", "isPartOf"],
    "ContactPage": ["url", "name", "isPartOf"],
    "ProfilePage": ["url", "name", "isPartOf", "mainEntity"],
    "Service": ["name", "provider"],
    "Organization": ["logo"],
    "BlogPosting": ["dateModified", "mainEntityOfPage"],
    "Article": ["dateModified", "mainEntityOfPage"],
}

DEPRECIES = {
    "HowTo": "Rich result déprécié en septembre 2023. Le balisage reste valide "
             "mais n'affiche plus rien dans Google.",
    "FAQPage": "Rich result restreint depuis août 2023 aux sites gouvernementaux "
               "et de santé reconnus. Reste utile pour les moteurs IA.",
    "SpecialAnnouncement": "Déprécié en juillet 2025.",
}

SENSIBLES = {
    "AggregateRating": "À n'utiliser que si les avis sont réels, visibles sur la "
                       "page et vérifiables. Une note inventée est un motif d'action manuelle.",
    "Review": "Idem : l'avis doit exister et être visible sur la page.",
}

LOGICIELS = {"SoftwareApplication", "WebApplication", "MobileApplication", "VideoGame"}
TYPES_PAGE = {"WebPage", "CollectionPage", "AboutPage", "ContactPage", "ProfilePage",
              "FAQPage", "ItemPage", "SearchResultsPage", "MedicalWebPage", "QAPage"}
# Types dont deux exemplaires sur une page créent une ambiguïté que Google
# résout en les ignorant : typiquement un plugin SEO et un thème.
UNIQUES = {"Article", "BlogPosting", "NewsArticle", "Organization", "WebSite", "Product"}

CLES_URL = {"url", "logo", "image", "sameAs", "item", "contentUrl", "thumbnailUrl",
            "embedUrl", "mainEntityOfPage", "@id", "downloadUrl", "installUrl"}
CLES_DATE = {"datePublished", "dateModified", "dateCreated", "uploadDate", "startDate",
             "endDate", "datePosted", "validThrough", "validFrom", "foundingDate",
             "birthDate", "priceValidUntil", "expires"}
DATE_ISO = re.compile(r"^\d{4}(?:-\d{2}(?:-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?"
                      r"(?:Z|[+-]\d{2}:?\d{2})?)?)?)?$")
# Une donnée non confirmée ne part jamais en production : Google ne distingue
# pas « A_CONFIRMER » d'une vraie valeur, il l'affiche.
PROVISOIRES = re.compile(r"A_CONFIRMER|À_CONFIRMER|\bTODO\b|\{\{.*?\}\}|\[à compléter\]|"
                         r"\bXXX\b|lorem ipsum|\[insérer", re.I)
WIKIDATA = re.compile(r"^https://www\.wikidata\.org/wiki/Q\d+$")
WIKIPEDIA = re.compile(r"^https://[a-z]{2,3}(?:-[a-z]+)?\.wikipedia\.org/wiki/\S+$")

MAX_ABOUT, MAX_MENTIONS, MAX_HEADLINE = 3, 12, 110


# ─── Extraction ───────────────────────────────────────────────────

class _Scripts(HTMLParser):
    """Collecte les <script type="application/ld+json"> sans dépendance."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocs: list[str] = []
        self._dans = False
        self._tampon: list[str] = []
        self.microdata = False
        self.rdfa = False

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if "itemscope" in a:
            self.microdata = True
        if "typeof" in a:
            self.rdfa = True
        if tag == "script" and a.get("type", "").strip().lower().startswith("application/ld+json"):
            self._dans, self._tampon = True, []

    def handle_endtag(self, tag):
        if tag == "script" and self._dans:
            self.blocs.append("".join(self._tampon))
            self._dans = False

    def handle_data(self, data):
        if self._dans:
            self._tampon.append(data)


def analyser_html(html: str) -> dict:
    p = _Scripts()
    p.feed(html)
    p.close()
    blocs, erreurs = [], []
    for i, brut in enumerate(p.blocs, 1):
        try:
            blocs.append(json.loads(brut))
        except json.JSONDecodeError as exc:
            erreurs.append(f"Bloc #{i} : JSON invalide — {exc}. Le bloc entier est ignoré par Google.")
    if p.microdata:
        erreurs.append("Microdata détecté. Google recommande JSON-LD — envisagez la migration.")
    if p.rdfa:
        erreurs.append("RDFa détecté. Google recommande JSON-LD.")
    return {"blocs": blocs, "erreurs": erreurs, "scripts": len(p.blocs), "html": True}


def extraire(source: str) -> dict:
    """Renvoie {blocs, erreurs, scripts, html}. Fichier JSON, fichier HTML ou URL."""
    chemin = Path(source)
    if chemin.exists():
        contenu = chemin.read_text(encoding="utf-8")
        if contenu.lstrip().startswith("<"):
            return analyser_html(contenu)
        try:
            return {"blocs": [json.loads(contenu)], "erreurs": [], "scripts": 1, "html": False}
        except json.JSONDecodeError as exc:
            return {"blocs": [], "erreurs": [f"JSON invalide : {exc}"], "scripts": 1, "html": False}

    try:
        import requests
    except ImportError:
        print("Pour valider une URL : pip install -r requirements.txt", file=sys.stderr)
        raise SystemExit(1)
    rep = requests.get(source, headers={"User-Agent": "ClaudeCodeSEODecupler/2.0"}, timeout=30)
    rep.raise_for_status()
    # HTML initial uniquement : un balisage injecté en JavaScript (GTM) n'y
    # figure pas, et c'est précisément ce qu'il faut voir.
    return analyser_html(rep.text)


# ─── Parcours du graphe ───────────────────────────────────────────

def types_de(noeud: dict) -> list[str]:
    t = noeud.get("@type")
    return [t] if isinstance(t, str) else [x for x in (t or []) if isinstance(x, str)]


def est_reference(valeur) -> bool:
    return isinstance(valeur, dict) and set(valeur) == {"@id"}


def liste(v) -> list:
    return v if isinstance(v, list) else ([] if v is None else [v])


def parcourir(bloc, chemin: tuple = ()):
    """Produit (nœud typé, chemin des clés qui y mènent), @graph compris."""
    if isinstance(bloc, list):
        for item in bloc:
            yield from parcourir(item, chemin)
    elif isinstance(bloc, dict):
        if "@type" in bloc:
            yield bloc, chemin
        for cle, valeur in bloc.items():
            if isinstance(valeur, (dict, list)):
                yield from parcourir(valeur, chemin if cle == "@graph" else chemin + (cle,))


def aplatir(bloc) -> list[dict]:
    """Déplie les @graph et les tableaux pour obtenir la liste des entités."""
    return [n for n, _ in parcourir(bloc)]


def valeurs(bloc, cle_parent: str = ""):
    """Toutes les chaînes du JSON, avec la clé qui les porte."""
    if isinstance(bloc, list):
        for item in bloc:
            yield from valeurs(item, cle_parent)
    elif isinstance(bloc, dict):
        for cle, valeur in bloc.items():
            yield from valeurs(valeur, cle)
    elif isinstance(bloc, str):
        yield cle_parent, bloc


def references(bloc):
    """Toutes les références {"@id": …} du JSON, avec la clé qui les porte."""
    if isinstance(bloc, list):
        for item in bloc:
            yield from references(item)
    elif isinstance(bloc, dict):
        for cle, valeur in bloc.items():
            for v in liste(valeur):
                if est_reference(v):
                    yield cle, v["@id"]
                elif isinstance(v, (dict, list)):
                    yield from references(v)


def empreinte(noeud: dict) -> str:
    return hashlib.sha256(json.dumps(noeud, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()[:12]


def cle_entite(e) -> str | None:
    """Identité d'une entité about/mentions : @id, sinon QID, sinon nom."""
    if not isinstance(e, dict):
        return str(e)
    if isinstance(e.get("@id"), str):
        return e["@id"]
    for s in liste(e.get("sameAs")):
        if isinstance(s, str) and "wikidata.org" in s:
            return s
    return e.get("name") if isinstance(e.get("name"), str) else None


# ─── Contrôles ────────────────────────────────────────────────────

def valider(entites: list[dict], blocs: list | None = None, chemins: list[tuple] | None = None,
            aujourdhui: dt.date | None = None) -> list[dict]:
    """Constats {gravite, type, message}. `blocs` active les contrôles de graphe."""
    constats: list[dict] = []
    types_vus: list[str] = []
    chemins = chemins or [()] * len(entites)

    def c(gravite, type_, message):
        constats.append({"gravite": gravite, "type": type_, "message": message})

    definis = {n["@id"]: n for n in entites if isinstance(n.get("@id"), str)}
    # Sujets principaux des nœuds de page : un logiciel y a sa place, pas ailleurs.
    cibles_main = {v["@id"] if est_reference(v) else id(v)
                   for n in entites if set(types_de(n)) & TYPES_PAGE
                   for v in liste(n.get("mainEntity")) if isinstance(v, dict)}

    for entite, chemin in zip(entites, chemins):
        types = types_de(entite)
        nom = types[0] if types else "?"
        for t in types:
            types_vus.append(t)
            manquantes = [p for p in REQUISES_GOOGLE.get(t, []) if p not in entite]
            if manquantes:
                c("erreur", t, f"Propriétés requises par Google manquantes : {', '.join(manquantes)}. "
                               "Sans elles, aucun rich result.")
            attendues = [p for p in ATTENDUES_METHODE.get(t, []) if p not in entite]
            if attendues and "@id" in entite:
                c("attention", t, f"Propriétés attendues par la méthode absentes : {', '.join(attendues)}. "
                                  "Le nœud existe mais ne se rattache pas complètement au graphe.")
            if t in DEPRECIES:
                c("info", t, DEPRECIES[t])
            if t in SENSIBLES:
                c("attention", t, SENSIBLES[t])

        if set(types) & LOGICIELS:
            cite = bool(set(chemin) & {"mentions", "about"})
            principal = entite.get("@id") in cibles_main or id(entite) in cibles_main
            if cite or not principal:
                c("attention", "/".join(sorted(set(types) & LOGICIELS)),
                  "Logiciel balisé en SoftwareApplication alors qu'il n'est pas le sujet de la page"
                  + (" (il est cité dans about/mentions)" if cite else "") + ". Google applique alors les "
                  "exigences du rich result Software App (offers, note ou avis) et remonte une erreur "
                  "critique en Search Console. Un logiciel cité se balise en Thing avec sameAs.")

        if {"Organization", "LocalBusiness"} & set(types) and ("aggregateRating" in entite or "review" in entite):
            c("attention", nom, "Note ou avis posés sur l'organisation elle-même : Google ignore les avis "
                                "auto-attribués et peut sanctionner le balisage.")
        if any(isinstance(a, dict) and "SearchAction" in types_de(a) for a in liste(entite.get("potentialAction"))):
            c("attention", "SearchAction", "Champ de recherche sitelinks retiré par Google en novembre 2024 : "
                                           "SearchAction n'apporte plus rien, à supprimer.")
        titre = entite.get("headline")
        if isinstance(titre, str) and len(titre) > MAX_HEADLINE:
            c("attention", nom, f"headline de {len(titre)} caractères : au-delà de {MAX_HEADLINE}, "
                                "Google l'ignore. Reprendre le H1.")

        about, mentions = liste(entite.get("about")), liste(entite.get("mentions"))
        if len(about) > MAX_ABOUT:
            c("attention", nom, f"{len(about)} entités en about : {MAX_ABOUT} maximum. Test : la page "
                                "devient-elle hors sujet sans cette entité ? Sinon, elle va en mentions.")
        if len(mentions) > MAX_MENTIONS:
            c("attention", nom, f"{len(mentions)} entités en mentions : {MAX_MENTIONS} maximum, "
                                "toutes visibles dans le contenu principal.")
        doublons = ({cle_entite(e) for e in about} & {cle_entite(e) for e in mentions}) - {None}
        if doublons:
            c("attention", nom, f"Entité à la fois en about et en mentions : {', '.join(sorted(doublons))}. "
                                "Choisir l'une des deux.")
        for v in liste(entite.get("hasPart")):
            cible = definis.get(v["@id"]) if est_reference(v) else v
            if isinstance(cible, dict) and "ItemList" in types_de(cible):
                c("attention", "ItemList", "ItemList relié par hasPart : une liste secondaire se relie par "
                                           "mentions (hasPart en ferait une partie éditoriale de la page).")

        debut, fin = entite.get("datePublished"), entite.get("dateModified")
        if isinstance(debut, str) and isinstance(fin, str) and DATE_ISO.match(debut) \
                and DATE_ISO.match(fin) and fin[:10] < debut[:10]:
            c("erreur", nom, f"dateModified ({fin}) antérieure à datePublished ({debut}).")

    # Doublons : très fréquent sur WordPress (plugin SEO + thème).
    for t in sorted(set(types_vus)):
        if types_vus.count(t) > 1 and t in UNIQUES:
            c("erreur", t, f"{types_vus.count(t)} entités « {t} » sur la même page. Google résout l'ambiguïté "
                           "en les ignorant. Cause fréquente : un plugin SEO et un thème qui posent chacun le "
                           "leur, ou un objet recopié en ligne au lieu d'une référence {\"@id\"}.")

    if blocs is not None:
        constats += controler_graphe(blocs, entites, aujourdhui)
    return constats


def controler_graphe(blocs: list, entites: list[dict], aujourdhui: dt.date | None = None) -> list[dict]:
    """@id, références, URL, dates, textes provisoires, sameAs."""
    constats: list[dict] = []
    aujourdhui = aujourdhui or dt.date.today()

    def c(gravite, type_, message):
        constats.append({"gravite": gravite, "type": type_, "message": message})

    # Un @id défini deux fois avec des contenus différents : deux entités
    # qui se disputent le même nom, Google en retient une au hasard.
    vus: dict[str, str] = {}
    for n in entites:
        i = n.get("@id")
        if not isinstance(i, str):
            continue
        h = empreinte(n)
        if i in vus and vus[i] != h:
            c("erreur", "@id", f"« {i} » défini plusieurs fois avec des contenus différents. Un @id désigne "
                               "une seule entité : la définir une fois, la référencer ailleurs.")
        vus.setdefault(i, h)

    signalees = set()
    for cle, ref in references(blocs):
        if ref not in vus and ref not in signalees:
            signalees.add(ref)
            c("erreur", "@id", f"Référence {cle} → « {ref} » introuvable dans le graphe de la page. Google "
                               "ne va pas chercher un nœud ailleurs : l'entité doit figurer dans le @graph.")

    for cle, v in valeurs(blocs):
        if PROVISOIRES.search(v):
            c("erreur", "Provisoire", f"{cle} = « {v[:60]} » : donnée non confirmée. Bloque la livraison.")
            continue
        if cle in CLES_URL:
            if not v.startswith(("http://", "https://")):
                c("erreur", "URL", f"{cle} = « {v[:80]} » : URL relative ou invalide. Toujours absolue, en https.")
            elif v.startswith("http://"):
                c("attention", "URL", f"{cle} = « {v[:80]} » : en http, à passer en https.")
        if cle in CLES_DATE:
            if not DATE_ISO.match(v):
                c("erreur", "Date", f"{cle} = « {v} » : format ISO 8601 attendu (AAAA-MM-JJ ou "
                                    "AAAA-MM-JJThh:mm:ss+01:00).")
            elif cle in {"datePublished", "dateModified"} and v[:10] > aujourdhui.isoformat():
                c("attention", "Date", f"{cle} = « {v} » dans le futur : la date doit refléter le contenu réel.")
        if cle == "sameAs" and v.startswith("http"):
            if "wikidata.org" in v and not WIKIDATA.match(v):
                c("attention", "sameAs", f"« {v} » : format Wikidata attendu https://www.wikidata.org/wiki/Q123.")
            elif "wikipedia.org" in v and not WIKIPEDIA.match(v):
                c("attention", "sameAs", f"« {v} » : format Wikipédia attendu https://fr.wikipedia.org/wiki/Titre.")
    return constats


def comparer_socle(entites: list[dict], socle) -> list[dict]:
    """Chaque nœud du socle de référence doit se retrouver à l'identique sur la page."""
    constats = []
    par_id = {n.get("@id"): n for n in entites if isinstance(n.get("@id"), str)}
    for ref in aplatir(socle):
        i = ref.get("@id")
        if not isinstance(i, str):
            continue
        page = par_id.get(i)
        t = "/".join(types_de(ref)) or "?"
        if page is None:
            constats.append({"gravite": "erreur", "type": t, "message": f"Nœud du socle « {i} » absent de la page."})
        elif empreinte(page) != empreinte(ref):
            ecarts = sorted(k for k in set(page) | set(ref) if page.get(k) != ref.get(k))
            constats.append({"gravite": "erreur", "type": t,
                             "message": f"« {i} » diverge du socle (empreinte {empreinte(page)} ≠ "
                                        f"{empreinte(ref)}) sur : {', '.join(ecarts)}. Le socle se régénère "
                                        "depuis le fichier source, jamais à la main page par page."})
    return constats


# ─── Sortie ───────────────────────────────────────────────────────

def controler(source: str, socle: str | None = None, aujourdhui: dt.date | None = None) -> dict:
    ext = extraire(source)
    paires = [p for b in ext["blocs"] for p in parcourir(b)]
    entites = [n for n, _ in paires]
    constats = []
    if ext["html"] and ext["scripts"] > 1:
        constats.append({"gravite": "attention", "type": "Page",
                         "message": f"{ext['scripts']} scripts JSON-LD sur la page. La méthode en veut un seul, "
                                    "avec un @graph : injectez vos nœuds dans le graphe du plugin SEO "
                                    "(filtres wpseo_schema_graph / rank_math/json_ld) plutôt qu'à côté."})
    constats += valider(entites, ext["blocs"], [ch for _, ch in paires], aujourdhui)
    if socle:
        constats += comparer_socle(entites, json.loads(Path(socle).read_text(encoding="utf-8")))
    types = sorted({t for e in entites for t in types_de(e)})
    noeuds = [{"type": "/".join(types_de(n)), "id": n.get("@id", "")} for n, ch in paires if not ch]
    return {"types": types, "entites": len(entites), "scripts": ext["scripts"], "noeuds": noeuds,
            "erreurs_parsing": ext["erreurs"], "constats": constats}


def main() -> int:
    p = argparse.ArgumentParser(description="Validation JSON-LD")
    p.add_argument("source", help="URL, fichier .html ou fichier .jsonld/.json")
    p.add_argument("--socle", help="socle-global.json : vérifie que les nœuds du socle sont identiques sur la page")
    p.add_argument("--strict", action="store_true", help="code de sortie 1 si une erreur est trouvée")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    r = controler(args.source, args.socle)
    bloquant = any("invalide" in e for e in r["erreurs_parsing"]) \
        or any(c["gravite"] == "erreur" for c in r["constats"])
    code = 1 if args.strict and (bloquant or not r["entites"]) else 0

    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return code

    print(f"\n{'═' * 60}")
    print(f"  Données structurées — {r['entites']} entité(s), {r['scripts']} script(s)")
    print(f"{'═' * 60}\n")

    if not r["entites"] and not r["erreurs_parsing"]:
        print("  🔴 Aucune donnée structurée trouvée.\n")
        print("  À poser en priorité : le socle Organization + WebSite,")
        print("  puis le nœud de page (WebPage, Service, BlogPosting…).\n")
        return code

    print(f"  Types détectés : {', '.join(r['types']) or 'aucun'}\n")
    if r["noeuds"]:
        print("  Nœuds présents :")
        for n in r["noeuds"]:
            print(f"    · {n['type']:<22} {n['id']}")
        print()

    for erreur in r["erreurs_parsing"]:
        print(f"  🔴 {erreur}\n")

    icones = {"erreur": "🔴", "attention": "🟠", "info": "ℹ️ "}
    for gravite in ("erreur", "attention", "info"):
        for c in (c for c in r["constats"] if c["gravite"] == gravite):
            print(f"  {icones[gravite]} {c['type']}")
            print(f"     {c['message']}\n")

    if not r["constats"] and not r["erreurs_parsing"]:
        print("  🟢 Aucun problème détecté.\n")

    print("  Vérifiez toujours que les valeurs du schema correspondent au")
    print("  contenu visible : un écart est un motif d'action manuelle.\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
