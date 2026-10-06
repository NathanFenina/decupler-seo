#!/usr/bin/env python3
"""WordPress par l'API REST : publier, mettre à jour, cartographier, mailler.

    python3 wp.py verifier
    python3 wp.py publier --html contenus/guide.html --titre "…" --slug guide \\
        --extrait "…" --categories "Guides" --image-une hero.webp --alt-image "…" \\
        --meta-titre "…" --meta-description "…"
    python3 wp.py media --fichier hero.webp --alt "…"
    python3 wp.py meta --url https://exemple.com/page/ --titre-seo "…" --description "…" --requete "…"
    python3 wp.py carte                        # → donnees/carte-contenu.csv
    python3 wp.py maillage                     # pages peu liées : qui devrait les lier
    python3 wp.py maillage --cible https://exemple.com/page/ --appliquer
    python3 wp.py maillage --html contenus/brouillon.html --titre "…"
    python3 wp.py remplacer --motif "<!-- cta -->.*?<!-- /cta -->" --par-fichier cta.html

Toutes les commandes d'écriture acceptent --simuler : rien n'est écrit, le
plan et le verdict du garde-fou sont affichés.

Identifiants, dans l'environnement ou le .env du projet : WP_SITE_URL,
WP_USER (ou WP_USERNAME) et WP_APP_PASSWORD — un mot de passe
d'application, jamais celui de connexion. Aucune valeur n'est jamais affichée.

Les règles, qui ne dépendent pas de la bonne volonté de l'appelant :
- Un contenu neuf part en brouillon (publication.statut_par_defaut).
- Une page déjà en ligne n'est jamais modifiée en direct sans --statut
  publish (ou --en-ligne) ET le feu vert de guard.py : sinon la modification
  part en révision (autosave), à valider dans l'éditeur WordPress.
- Le fichier à publier passe controle_contenu.py, bloquant.
- Tout contenu existant est sauvegardé avant écriture, dans le dossier d'état
  du projet, restaurable par cms_restore.py.
- Toute modification mise en ligne est journalisée (journal.py ajouter),
  avec sa valeur d'avant : sans elle, pas de mesure à J+28 ni de retour arrière.

Bibliothèque standard uniquement : ce script tourne dans les routines cloud.
"""

from __future__ import annotations

import argparse
import base64
import csv
import datetime as dt
import html as html_lib
import json
import mimetypes
import os
import re
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlencode, urljoin, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import charger_env, dossier_etat, lire_valeur, racine_projet  # noqa: E402

SCRIPTS = Path(__file__).resolve().parent
AGENT = "seo-wp/1.0 (python-urllib)"
ESSAIS = 5

# Les champs SEO ne sont pas dans `content` : chaque extension a les siens,
# et ils ne sont écrivables par l'API que s'ils y sont exposés.
CHAMPS_SEO = {
    "yoast": {"titre": "_yoast_wpseo_title", "description": "_yoast_wpseo_metadesc"},
    "rankmath": {"titre": "rank_math_title", "description": "rank_math_description"},
    "seopress": {"titre": "_seopress_titles_title", "description": "_seopress_titles_desc"},
}
NAMESPACES_SEO = (("yoast", "yoast/v1"), ("rankmath", "rankmath/v1"), ("seopress", "seopress/v1"))
# Le mu-plugin qui ouvre ces champs à l'API (Yoast, Rank Math, SEOPress) :
# à côté de scripts/, dans le plugin comme dans un projet (.claude/decupler-seo/).
MU_PLUGIN_SEO = SCRIPTS.parent / "templates" / "wordpress" / "mu-plugins" / "seo-meta-rest.php"

META_MIN, META_MAX = 120, 156      # la zone verte de la méthode, partout
TITRE_MAX = 60
STATUTS = ("draft", "pending", "publish")
STATUTS_BROUILLON = {"draft", "pending", "auto-draft", "future", "private"}

MOTS_VIDES = {
    "le", "la", "les", "un", "une", "des", "de", "du", "d", "l", "au", "aux", "a", "et", "ou",
    "en", "sur", "sous", "pour", "par", "avec", "sans", "dans", "ce", "ces", "cet", "cette",
    "se", "sa", "son", "ses", "que", "qui", "quoi", "quel", "quelle", "quels", "quelles",
    "est", "sont", "etre", "plus", "moins", "votre", "vos", "notre", "nos", "mon", "ma", "mes",
    "leur", "leurs", "tout", "tous", "toute", "toutes", "comment", "pourquoi", "quand", "ne",
    "pas", "il", "elle", "ils", "on", "nous", "vous", "je", "tu", "y", "the", "of", "for",
    "to", "in", "and", "or", "is", "an", "how", "what", "faire", "bien", "tres", "entre",
}


class ErreurWP(Exception):
    """Erreur présentable telle quelle : elle dit quoi faire, sans secret."""


class ErreurConnexion(ErreurWP):
    """Le serveur n'a pas répondu : on ne sait pas si l'écriture a eu lieu."""


# ═══════════════════════════════════════════════════════════════════
# Fonctions pures — testées hors ligne
# ═══════════════════════════════════════════════════════════════════

def _sans_accents(texte: str) -> str:
    """Retire les accents caractère par caractère : la longueur est conservée,
    ce qui permet de retrouver dans le texte d'origine ce qu'on a trouvé dans
    sa version normalisée."""
    sortie = []
    for c in texte:
        if c in "’‘":
            sortie.append("'")
            continue
        decompose = unicodedata.normalize("NFKD", c)
        sortie.append(decompose[0] if decompose else c)
    return "".join(sortie)


def slugifier(texte: str, longueur_max: int = 70) -> str:
    """Slug lisible : minuscules, sans accents, tirets, coupé sur un tiret."""
    t = texte.lower().replace("œ", "oe").replace("æ", "ae").replace("’", "-")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    if len(t) > longueur_max:
        t = t[:longueur_max + 1].rsplit("-", 1)[0] if "-" in t[:longueur_max + 1] else t[:longueur_max]
    return t.strip("-")


def cle_url(url: str) -> str:
    """Clé de comparaison d'URL : hôte sans www, chemin sans barre finale."""
    p = urlparse(url.strip())
    hote = p.netloc.lower().removeprefix("www.")
    chemin = unquote(p.path).rstrip("/") or "/"
    return hote + chemin


def texte_brut(fragment: str) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", " ", fragment or ""))).strip()


def _champ_rendu(valeur) -> str:
    """title/excerpt/content arrivent en {raw, rendered} ou en chaîne."""
    if isinstance(valeur, dict):
        return valeur.get("rendered") or valeur.get("raw") or ""
    return valeur or ""


def _champ_brut(valeur) -> str:
    """Uniquement `raw` : `rendered` d'un extrait vide est l'extrait
    auto-généré depuis le contenu, qui n'est pas ce qui a été écrit."""
    if isinstance(valeur, dict):
        return valeur.get("raw") or ""
    return valeur or ""


def construire_charge(titre: str | None = None, html: str | None = None, statut: str | None = None,
                      slug: str | None = None, extrait: str | None = None,
                      categories: list[int] | None = None, etiquettes: list[int] | None = None,
                      image_une: int | None = None, meta: dict | None = None) -> dict:
    """Charge JSON d'un POST /wp/v2/<type> : uniquement les champs fournis.

    Envoyer un champ non voulu écrase ce qui a été modifié entre-temps dans
    l'éditeur — et envoyer `status` par défaut sur une mise à jour
    dépublierait une page en ligne.
    """
    charge: dict = {}
    for cle, valeur in (("title", titre), ("content", html), ("status", statut), ("slug", slug),
                        ("excerpt", extrait), ("featured_media", image_une)):
        if valeur is not None:
            charge[cle] = valeur
    if categories:
        charge["categories"] = categories
    if etiquettes:
        charge["tags"] = etiquettes
    if meta:
        charge["meta"] = meta
    return charge


def detecter_plugin_seo(namespaces: list[str]) -> str | None:
    presents = [nom for nom, ns in NAMESPACES_SEO if ns in (namespaces or [])]
    return presents[0] if presents else None


def charge_meta_seo(plugin: str | None, titre: str | None = None, description: str | None = None) -> dict:
    """{champ: valeur} pour l'extension SEO détectée ; vide sans extension."""
    if plugin not in CHAMPS_SEO:
        return {}
    champs = CHAMPS_SEO[plugin]
    meta = {}
    if titre is not None:
        meta[champs["titre"]] = titre
    if description is not None:
        meta[champs["description"]] = description
    return meta


def meta_non_ecrits(reponse: dict, attendus: dict) -> list[str]:
    """Champs envoyés que la réponse ne reflète pas.

    WordPress ignore sans erreur un champ meta non exposé dans l'API : un 200
    ne prouve rien, seule la valeur relue compte.
    """
    lus = (reponse or {}).get("meta") or {}
    if not isinstance(lus, dict):
        lus = {}
    return [cle for cle, valeur in attendus.items() if lus.get(cle) != valeur]


def lire_seo_champs(item: dict, plugin: str | None) -> dict:
    """Valeurs brutes des champs SEO exposés (vide = le modèle de l'extension s'applique)."""
    meta = item.get("meta") or {}
    if plugin not in CHAMPS_SEO or not isinstance(meta, dict):
        return {}
    return {c: meta[c] for c in CHAMPS_SEO[plugin].values() if c in meta}


def lire_seo_affiche(item: dict) -> tuple[str, str]:
    """Title et meta description réellement servis, quand Yoast les expose."""
    tete = item.get("yoast_head_json") or {}
    if not isinstance(tete, dict):
        return "", ""
    return html_lib.unescape(tete.get("title") or ""), html_lib.unescape(tete.get("description") or "")


class _LecteurHead(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.dans_title = False
        self.title = ""
        self.description = ""
        self.canonical = ""
        self.robots = ""

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        if tag == "title":
            self.dans_title = True
        elif tag == "meta" and a.get("name", "").lower() == "description" and not self.description:
            self.description = a.get("content", "").strip()
        elif tag == "meta" and a.get("name", "").lower() == "robots":
            self.robots = a.get("content", "").strip()
        elif tag == "link" and "canonical" in a.get("rel", "").lower().split():
            self.canonical = a.get("href", "").strip()

    def handle_endtag(self, tag):
        if tag == "title":
            self.dans_title = False

    def handle_data(self, data):
        if self.dans_title and not self.title:
            self.title = data.strip()


def extraire_head(page_html: str) -> dict:
    lecteur = _LecteurHead()
    lecteur.feed(page_html)
    return {"title": lecteur.title, "description": lecteur.description,
            "canonical": lecteur.canonical, "robots": lecteur.robots}


class _LecteurContenu(HTMLParser):
    IGNORES = {"script", "style", "noscript", "template", "svg"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ignore = 0
        self.titre_en_cours: str | None = None
        self.tampon: list[str] = []
        self.textes: list[str] = []
        self.titres: dict[str, list[str]] = {"h1": [], "h2": []}
        self.liens: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self.IGNORES:
            self.ignore += 1
        elif tag in ("h1", "h2"):
            self.titre_en_cours, self.tampon = tag, []
        elif tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.liens.append(href.strip())

    def handle_endtag(self, tag):
        if tag in self.IGNORES and self.ignore:
            self.ignore -= 1
        elif tag == self.titre_en_cours:
            self.titres[tag].append(re.sub(r"\s+", " ", "".join(self.tampon)).strip())
            self.titre_en_cours = None

    def handle_data(self, data):
        if self.ignore:
            return
        self.textes.append(data)
        if self.titre_en_cours:
            self.tampon.append(data)


def lien_interne(href: str, site: str) -> str | None:
    """URL absolue sans fragment ni paramètres si le lien reste sur le site, sinon None."""
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    absolue = urljoin(site.rstrip("/") + "/", href)
    p = urlparse(absolue)
    if p.scheme not in ("http", "https"):
        return None
    if p.netloc.lower().removeprefix("www.") != urlparse(site).netloc.lower().removeprefix("www."):
        return None
    if re.match(r"/(wp-content|wp-admin|wp-json|wp-includes|feed)(/|$)", p.path) or p.path.endswith("/feed/"):
        return None
    return f"{p.scheme}://{p.netloc}{p.path or '/'}"


def analyser_contenu(contenu_html: str, site: str) -> dict:
    """H1, H2, nombre de mots et liens du CORPS de la page — pas du menu ni du
    pied de page : c'est le maillage contextuel, celui qui transmet."""
    lecteur = _LecteurContenu()
    lecteur.feed(contenu_html or "")
    texte = " ".join(lecteur.textes)
    mots = re.findall(r"[^\W_]+(?:['’-][^\W_]+)*", texte)
    internes, externes = [], 0
    for href in lecteur.liens:
        interne = lien_interne(href, site)
        if interne:
            if interne not in internes:
                internes.append(interne)
        elif href.startswith(("http://", "https://")) and \
                urlparse(href).netloc.lower().removeprefix("www.") != urlparse(site).netloc.lower().removeprefix("www."):
            externes += 1
    return {"h1": lecteur.titres["h1"], "h2": [h for h in lecteur.titres["h2"] if h],
            "nb_mots": len(mots), "liens_internes": internes, "nb_liens_externes": externes,
            "termes": termes_principaux(texte)}


COLONNES_CARTE = ["id", "type", "statut", "url", "titre", "meta_titre", "meta_description", "h1", "h2",
                  "termes", "nb_mots", "nb_liens_internes", "liens_internes", "nb_liens_externes", "liens_entrants",
                  "modifie"]


def ligne_carte(item: dict, site: str, type_rest: str, plugin: str | None = None) -> dict:
    """Une ligne de la carte de contenu depuis la réponse REST d'un article ou d'une page."""
    analyse = analyser_contenu(_champ_rendu(item.get("content")), site)
    meta_titre, meta_desc = lire_seo_affiche(item)
    champs = lire_seo_champs(item, plugin)
    if plugin in CHAMPS_SEO:
        meta_titre = meta_titre or champs.get(CHAMPS_SEO[plugin]["titre"], "")
        meta_desc = meta_desc or champs.get(CHAMPS_SEO[plugin]["description"], "")
    internes = [u for u in analyse["liens_internes"] if cle_url(u) != cle_url(item.get("link", ""))]
    return {
        "id": item.get("id", ""),
        "type": type_rest,
        "statut": item.get("status", ""),
        "url": item.get("link", ""),
        "titre": texte_brut(_champ_rendu(item.get("title"))),
        "meta_titre": meta_titre,
        "meta_description": meta_desc,
        "h1": " | ".join(analyse["h1"]),
        "h2": " | ".join(analyse["h2"]),
        "termes": " ".join(analyse["termes"]),
        "nb_mots": analyse["nb_mots"],
        "nb_liens_internes": len(internes),
        "liens_internes": " ".join(internes),
        "nb_liens_externes": analyse["nb_liens_externes"],
        "liens_entrants": 0,
        "modifie": (item.get("modified") or "")[:10],
    }


def calculer_entrants(lignes: list[dict]) -> list[dict]:
    """Nombre de pages de la carte dont le corps lie chaque page."""
    compte: dict[str, int] = {}
    for ligne in lignes:
        for cible in _liste_liens(ligne):
            compte[cle_url(cible)] = compte.get(cle_url(cible), 0) + 1
    for ligne in lignes:
        ligne["liens_entrants"] = compte.get(cle_url(ligne["url"]), 0)
    return lignes


def _liste_liens(ligne: dict) -> list[str]:
    liens = ligne.get("liens_internes") or []
    return liens.split() if isinstance(liens, str) else list(liens)


def _mots_porteurs(texte: str):
    """Mots porteurs de sens, sans accents ni pluriel simple, dans l'ordre du texte."""
    t = _sans_accents((texte or "").replace("œ", "oe")).lower()
    for mot in re.findall(r"[a-z0-9]+", t):
        if len(mot) < 2 or mot in MOTS_VIDES or mot.isdigit():
            continue
        yield mot[:-1] if len(mot) > 4 and mot[-1] in "sx" else mot


def jetons(texte: str) -> set[str]:
    return set(_mots_porteurs(texte))


def termes_principaux(texte: str, nombre: int = 25) -> list[str]:
    """Les mots les plus fréquents du corps : le sujet réel de la page, que
    titre et H2 ne disent qu'en partie. Garder le texte entier alourdirait
    la carte sans rien apporter au rapprochement des pages."""
    compte: dict[str, int] = {}
    for mot in _mots_porteurs(texte):
        compte[mot] = compte.get(mot, 0) + 1
    return [m for m, _ in sorted(compte.items(), key=lambda x: (-x[1], x[0]))[:nombre]]


def _mots_slug(url: str) -> str:
    dernier = unquote(urlparse(url).path).rstrip("/").rsplit("/", 1)[-1]
    return dernier.replace("-", " ")


def sujet_coeur(ligne: dict) -> set[str]:
    """Le sujet d'une page, resserré : titre et slug."""
    return jetons(f"{ligne.get('titre', '')} {_mots_slug(ligne.get('url', ''))}")


def sujet_complet(ligne: dict) -> set[str]:
    """Tout ce dont la page parle, d'après la carte."""
    return jetons(" ".join(str(ligne.get(c, "")) for c in ("titre", "meta_titre", "meta_description", "h1", "h2",
                                                           "termes"))
                  + " " + _mots_slug(ligne.get("url", "")))


def mots_communs_au_site(lignes: list[dict], part: float = 0.5) -> set[str]:
    """Mots présents dans plus de la moitié des pages (marque, ville, métier) :
    ils rapprocheraient toutes les pages entre elles sans rien dire du sujet."""
    if len(lignes) < 4:
        return set()
    frequence: dict[str, int] = {}
    for ligne in lignes:
        for mot in sujet_complet(ligne):
            frequence[mot] = frequence.get(mot, 0) + 1
    return {m for m, n in frequence.items() if n > part * len(lignes)}


def pertinence(coeur_cible: set[str], sujet_source: set[str]) -> float:
    """Part du sujet de la cible que la source traite. 0 à 1.

    Asymétrique exprès : une page large qui couvre le sujet d'une page
    précise doit la lier ; l'inverse n'est pas vrai.
    """
    if not coeur_cible:
        return 0.0
    communs = coeur_cible & sujet_source
    if len(communs) < min(2, len(coeur_cible)):
        return 0.0
    return len(communs) / len(coeur_cible)


def ancres_candidates(ligne: dict) -> list[str]:
    """Ancres possibles, de la plus descriptive à la plus courte. Jamais « cliquez ici »."""
    candidates = []
    for source in (ligne.get("titre", ""), ligne.get("meta_titre", "")):
        court = re.split(r"\s+[|–—:-]\s+|\s*[|:?!]\s*", source or "")[0].strip()
        if court:
            candidates.append(court)
    candidates.append(_mots_slug(ligne.get("url", "")))
    vues, sortie = set(), []
    for c in candidates:
        cle = _sans_accents(c.lower())
        if 3 <= len(c) <= 80 and cle not in vues and len(jetons(c)) >= 1:
            vues.add(cle)
            sortie.append(c)
    return sorted(sortie, key=len, reverse=True)


def ancre_suggeree(ligne: dict) -> str:
    candidates = ancres_candidates(ligne)
    courtes = [c for c in candidates if len(c) <= 60]
    return (courtes or candidates or [""])[0]


def suggerer_liens(lignes: list[dict], cible: str | None = None, max_par_cible: int = 5,
                   seuil: float = 0.5, entrants_max: int = 1) -> list[dict]:
    """Liens entrants à poser : quelles pages devraient lier quelle cible.

    Sans cible : les pages qui reçoivent au plus `entrants_max` liens depuis
    le corps des autres pages (orphelines et quasi-orphelines).
    """
    communs_site = mots_communs_au_site(lignes)
    if cible:
        cibles = [l for l in lignes if cle_url(l["url"]) == cle_url(cible)]
    else:
        cibles = [l for l in lignes if int(l.get("liens_entrants") or 0) <= entrants_max]
    suggestions = []
    for c in cibles:
        coeur = sujet_coeur(c) - communs_site or sujet_coeur(c)
        candidats = []
        for s in lignes:
            if cle_url(s["url"]) == cle_url(c["url"]):
                continue
            if cle_url(c["url"]) in {cle_url(u) for u in _liste_liens(s)}:
                continue                                    # déjà lié
            score = pertinence(coeur, sujet_complet(s))
            if score >= seuil:
                candidats.append((score, int(s.get("nb_mots") or 0), s))
        candidats.sort(key=lambda x: (x[0], x[1]), reverse=True)
        for score, _, s in candidats[:max_par_cible]:
            suggestions.append({
                "source": s["url"], "source_id": s.get("id", ""), "source_type": s.get("type", ""),
                "source_statut": s.get("statut", ""), "cible": c["url"], "ancre": ancre_suggeree(c),
                "score": round(score, 2), "mots_communs": " ".join(sorted(coeur & sujet_complet(s))),
            })
    return suggestions


def suggerer_sortants(brouillon: dict, lignes: list[dict], max_liens: int = 8, seuil: float = 0.5) -> list[dict]:
    """Pages existantes qu'un nouveau contenu devrait lier."""
    communs_site = mots_communs_au_site(lignes)
    sujet = sujet_complet(brouillon)
    deja = {cle_url(u) for u in _liste_liens(brouillon)}
    retenus = []
    for c in lignes:
        if cle_url(c["url"]) in deja:
            continue
        coeur = sujet_coeur(c) - communs_site or sujet_coeur(c)
        score = pertinence(coeur, sujet)
        if score >= seuil:
            retenus.append({"cible": c["url"], "ancre": ancre_suggeree(c), "score": round(score, 2),
                            "entrants": int(c.get("liens_entrants") or 0)})
    # À pertinence égale, la page la moins liée d'abord : c'est elle qui en a besoin.
    retenus.sort(key=lambda r: (-r["score"], r["entrants"]))
    return retenus[:max_liens]


def recouvrement(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def doublons_potentiels(lignes: list[dict], seuil: float = 0.6) -> list[tuple[float, dict, dict]]:
    """Paires de pages au sujet presque identique : risque de cannibalisation."""
    communs_site = mots_communs_au_site(lignes)
    sujets = [(l, sujet_coeur(l) - communs_site) for l in lignes]
    paires = []
    for i, (a, sa) in enumerate(sujets):
        for b, sb in sujets[i + 1:]:
            if len(sa) >= 2 and len(sb) >= 2:
                r = recouvrement(sa, sb)
                if r >= seuil:
                    paires.append((round(r, 2), a, b))
    return sorted(paires, key=lambda p: -p[0])


def cannibalisation(brouillon: dict, lignes: list[dict], seuil: float = 0.8) -> list[tuple[float, dict]]:
    """Pages existantes qui couvrent déjà le sujet d'un nouveau contenu."""
    communs_site = mots_communs_au_site(lignes)
    coeur = sujet_coeur(brouillon) - communs_site or sujet_coeur(brouillon)
    touches = []
    for l in lignes:
        r = pertinence(coeur, sujet_coeur(l) | jetons(l.get("meta_titre", "")))
        if r >= seuil:
            touches.append((round(r, 2), l))
    return sorted(touches, key=lambda t: -t[0])


BALISES_SANS_LIEN = {"a", "h1", "h2", "h3", "h4", "h5", "h6", "script", "style", "code", "pre", "button",
                     "textarea", "title", "noscript", "label", "select", "option", "svg", "figcaption"}


def deja_lie(contenu_html: str, url: str, site: str) -> bool:
    cible = cle_url(url)
    for href in re.findall(r"""href\s*=\s*["']([^"']+)["']""", contenu_html or "", flags=re.I):
        interne = lien_interne(html_lib.unescape(href), site)
        if interne and cle_url(interne) == cible:
            return True
    return False


def inserer_lien(contenu_html: str, ancres: list[str], url: str) -> tuple[str, str | None]:
    """Pose un lien sur la première occurrence d'une des ancres dans le texte.

    Jamais dans un titre, un lien existant, un script, un bouton. Insensible
    à la casse et aux accents, mais le texte d'origine est conservé tel quel.
    Aucune phrase n'est inventée : si aucune ancre n'apparaît, rien n'est
    modifié et le lien est à placer à la main.
    """
    morceaux = re.split(r"(<[^>]*>)", contenu_html)
    for ancre in ancres:
        mots = _sans_accents(ancre).lower().split()
        if not mots:
            continue
        motif = re.compile(r"(?<![a-z0-9])" + r"\s+".join(re.escape(m) for m in mots) + r"(?![a-z0-9])")
        profondeur = 0
        for i, morceau in enumerate(morceaux):
            if morceau.startswith("<"):
                balise = re.match(r"<\s*(/?)\s*([a-zA-Z][a-zA-Z0-9]*)", morceau)
                if balise and balise.group(2).lower() in BALISES_SANS_LIEN and not morceau.endswith("/>"):
                    profondeur += -1 if balise.group(1) else 1
                    profondeur = max(profondeur, 0)
                continue
            if profondeur or not morceau.strip():
                continue
            trouve = motif.search(_sans_accents(morceau).lower())
            if trouve:
                debut, fin = trouve.span()
                href = html_lib.escape(url, quote=True)
                morceaux[i] = f'{morceau[:debut]}<a href="{href}">{morceau[debut:fin]}</a>{morceau[fin:]}'
                return "".join(morceaux), morceau[debut:fin]
    return contenu_html, None


def durcir_html(contenu_html: str) -> str:
    """Rend le HTML insensible à wpautop.

    Sur un contenu classique, WordPress coupe en paragraphes sur chaque ligne
    vide — y compris À L'INTÉRIEUR d'un <style> ou d'un <script>. Le
    navigateur abandonne alors le reste de la feuille de style, ou le script
    ne s'exécute plus. Une page parfaite en local sort cassée en ligne.
    """
    def sans_lignes_vides(m):
        return m.group(1) + re.sub(r"\n\s*\n+", "\n", m.group(2)) + m.group(3)
    for balise in ("style", "script"):
        contenu_html = re.sub(rf"(<{balise}\b[^>]*>)(.*?)(</{balise}>)", sans_lignes_vides, contenu_html,
                              flags=re.S | re.I)
    # Un <noscript> multiligne est coupé en deux : sa feuille de secours s'applique alors tout le temps.
    return re.sub(r"(<noscript>)(.*?)(</noscript>)",
                  lambda m: m.group(1) + re.sub(r"\s*\n\s*", "", m.group(2)) + m.group(3),
                  contenu_html, flags=re.S | re.I)


def problemes_meta(titre: str | None, description: str | None) -> list[str]:
    problemes = []
    if description is not None and not META_MIN <= len(description) <= META_MAX:
        problemes.append(f"meta description de {len(description)} caractères, hors de la zone "
                         f"{META_MIN}-{META_MAX}")
    if titre is not None and not titre.strip():
        problemes.append("title vide")
    elif titre is not None and len(titre) > TITRE_MAX:
        problemes.append(f"title de {len(titre)} caractères, coupé au-delà d'environ {TITRE_MAX}")
    return problemes


def decision_ecriture(verdict: str, valide: bool) -> tuple[bool, str]:
    """Traduit le verdict de guard.py. --valide n'est légitime qu'après un
    « oui » explicite d'un humain dans la conversation."""
    if verdict == "AUTORISE":
        return True, "garde-fou : autorisé"
    if verdict == "DEMANDE_VALIDATION":
        if valide:
            return True, "garde-fou : validation humaine déclarée (--valide)"
        return False, ("garde-fou : validation requise. Présentez le plan (--simuler), obtenez un oui "
                       "explicite, puis relancez avec --valide.")
    return False, "garde-fou : bloqué"


def mode_ecriture(statut_actuel: str | None, statut_demande: str | None) -> str:
    """creation | brouillon | revision | en-ligne.

    Une page en ligne n'est modifiée en direct que sur demande explicite ;
    sinon la modification part en révision, visible dans l'éditeur, sans
    toucher à ce que voient les visiteurs.
    """
    if statut_actuel is None:
        return "creation"
    if statut_actuel == "publish":
        return "en-ligne" if statut_demande == "publish" else "revision"
    return "brouillon"


def message_erreur(statut: int, corps: bytes | str | None, chemin: str = "") -> str:
    """Message d'erreur qui dit quoi faire. Ne contient jamais d'identifiant."""
    texte = corps.decode("utf-8", "replace") if isinstance(corps, bytes) else (corps or "")
    code, message = "", ""
    try:
        donnees = json.loads(texte)
        if isinstance(donnees, dict):
            code, message = str(donnees.get("code", "")), texte_brut(str(donnees.get("message", "")))
    except ValueError:
        pass
    detail = f" [{code}]" if code else ""
    serveur = f" Réponse du serveur : {message[:300]}" if message else ""
    if statut == 401:
        return (f"WordPress refuse les identifiants (401{detail}). Vérifiez : 1) WP_APP_PASSWORD est un "
                "mot de passe d'application (Utilisateurs → Profil → Mots de passe d'application), pas le "
                "mot de passe de connexion ; 2) WP_USER est l'identifiant de ce même compte ; 3) si les deux "
                "sont bons, l'hébergeur retire l'en-tête Authorization — ajoutez au .htaccess : "
                'SetEnvIf Authorization "(.*)" HTTP_AUTHORIZATION=$1.' + serveur)
    if statut == 403:
        return (f"Accès refusé (403{detail}) sur {chemin}. Soit le compte n'a pas le droit — rôle Éditeur ou "
                "Administrateur pour les pages, la publication et les contenus des autres ; soit un pare-feu "
                "(extension de sécurité, Cloudflare, hébergeur) bloque /wp-json/ : autorisez-le." + serveur)
    if statut == 404:
        if code == "rest_no_route":
            return (f"Route introuvable ({chemin}) : l'extension qui la fournit n'est pas active ou "
                    "n'expose pas cette route." + serveur)
        if not code:
            return ("L'API REST ne répond pas sur /wp-json/. Vérifiez WP_SITE_URL (https, www) et que les "
                    "permaliens ne sont pas réglés sur « Simple » (Réglages → Permaliens).")
        return f"Contenu introuvable ({chemin}{detail}) : vérifiez l'ID et le type (post ou page)." + serveur
    if statut == 413:
        return "Fichier trop lourd pour le serveur (413) : compressez l'image (WebP, 1600 px de large suffisent)."
    if statut == 400:
        return f"Requête refusée par WordPress (400{detail}).{serveur}"
    if statut >= 500:
        return (f"Erreur du serveur WordPress ({statut}{detail}) : réessayez plus tard ; si elle persiste, "
                "consultez les journaux PHP de l'hébergeur." + serveur)
    return f"Réponse inattendue de WordPress ({statut}{detail}).{serveur}"


def commande_journal(url: str, type_modif: str, avant: str, apres: str, requete: str | None = None,
                     auto: bool = False, note: str | None = None) -> list[str]:
    cmd = [sys.executable, str(SCRIPTS / "journal.py"), "ajouter", "--url", url, "--type", type_modif,
           "--avant", avant, "--apres", apres]
    if requete:
        cmd += ["--requete", requete]
    if note:
        cmd += ["--note", note]
    if auto:
        cmd.append("--auto")
    return cmd


def donnees_sauvegarde(item: dict, type_rest: str, plugin: str | None, maintenant: dt.datetime) -> dict:
    """État restaurable par cms_restore.py : les valeurs BRUTES, pas le rendu."""
    sauvegarde = {
        "cms": "wordpress", "type": type_rest, "id": item.get("id"), "url": item.get("link", ""),
        "titre": texte_brut(_champ_rendu(item.get("title"))), "date": maintenant.isoformat(timespec="seconds"),
        "title": _champ_brut(item.get("title")), "content": _champ_brut(item.get("content")),
        "excerpt": _champ_brut(item.get("excerpt")), "status": item.get("status", ""),
        "slug": item.get("slug", ""), "categories": item.get("categories", []), "tags": item.get("tags", []),
        "featured_media": item.get("featured_media", 0),
    }
    champs = lire_seo_champs(item, plugin)
    if champs:
        sauvegarde["meta"] = champs
    sauvegarde = {k: v for k, v in sauvegarde.items() if v is not None and not (k in ("categories", "tags") and v == [])}
    return sauvegarde


def nom_sauvegarde(item: dict, maintenant: dt.datetime) -> str:
    return f"{maintenant:%Y-%m-%d-%H%M%S}-{slugifier(item.get('slug') or '') or item.get('id', 'contenu')}.json"


# ═══════════════════════════════════════════════════════════════════
# Accès au site
# ═══════════════════════════════════════════════════════════════════

def transport_urllib(methode: str, url: str, corps: bytes | None, entetes: dict,
                     delai: int = 90) -> tuple[int, dict, bytes]:
    requete = urllib.request.Request(url, data=corps, method=methode, headers=entetes)
    try:
        with urllib.request.urlopen(requete, timeout=delai) as r:
            return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read()
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, e.read() or b""


class ClientWP:
    """Client REST minimal. Le transport est injectable : les tests n'appellent aucun site."""

    def __init__(self, site: str, utilisateur: str, mot_de_passe: str, transport=None, attendre=time.sleep):
        self.site = site.rstrip("/")
        jeton = base64.b64encode(f"{utilisateur}:{mot_de_passe.replace(' ', '')}".encode()).decode()
        self.__auth = f"Basic {jeton}"
        self._transport = transport or transport_urllib
        self._attendre = attendre

    def __repr__(self) -> str:
        return f"ClientWP({self.site})"

    def url(self, chemin: str, params: dict | None = None) -> str:
        base = f"{self.site}/wp-json{chemin}" if chemin.startswith("/") else chemin
        return base + ("?" + urlencode(params, doseq=True) if params else "")

    def appel(self, methode: str, chemin: str, params: dict | None = None, json_=None, corps: bytes | None = None,
              entetes: dict | None = None, reessayer: bool = True, auth: bool = True):
        """Renvoie (données JSON, en-têtes). Retente les coupures réseau et les
        502-504 — certains hébergeurs coupent par intermittence sur les pages
        lourdes —, jamais une erreur 4xx."""
        url = self.url(chemin, params)
        h = {"User-Agent": AGENT, "Accept": "application/json"}
        if auth:
            h["Authorization"] = self.__auth
        if json_ is not None:
            corps = json.dumps(json_, ensure_ascii=False).encode("utf-8")
            h["Content-Type"] = "application/json; charset=utf-8"
        h.update(entetes or {})
        essais = ESSAIS if reessayer else 1
        for essai in range(essais):
            try:
                statut, reponse_entetes, contenu = self._transport(methode, url, corps, h)
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
                if essai == essais - 1:
                    raise ErreurConnexion(f"Pas de réponse de {urlparse(url).netloc} après {essais} essai(s) : "
                                          f"{getattr(exc, 'reason', exc)}") from None
                self._attendre(2 ** essai)
                continue
            if statut in (502, 503, 504) and essai < essais - 1:
                self._attendre(2 ** essai)
                continue
            if statut >= 400:
                raise ErreurWP(message_erreur(statut, contenu, urlparse(url).path))
            if not contenu:
                return None, reponse_entetes
            try:
                return json.loads(contenu.decode("utf-8-sig")), reponse_entetes
            except ValueError:
                if chemin.startswith("/"):
                    raise ErreurWP("La réponse n'est pas du JSON : l'API REST est désactivée, redirigée ou "
                                   "interceptée (page de maintenance, pare-feu). Ouvrez "
                                   f"{self.site}/wp-json/ dans un navigateur pour voir ce qui répond.") from None
                return contenu.decode("utf-8", "replace"), reponse_entetes
        raise ErreurConnexion("Pas de réponse du serveur.")

    def get(self, chemin: str, **params):
        return self.appel("GET", chemin, params=params or None)[0]

    def post(self, chemin: str, donnees: dict, reessayer: bool = True):
        return self.appel("POST", chemin, json_=donnees, reessayer=reessayer)[0]

    def lister(self, chemin: str, params: dict | None = None, par_page: int = 100):
        """Tous les éléments d'une collection, page après page (X-WP-TotalPages)."""
        page = 1
        while True:
            try:
                lot, entetes = self.appel("GET", chemin, params={**(params or {}), "per_page": par_page, "page": page})
            except ErreurWP as exc:
                if "rest_post_invalid_page_number" in str(exc):
                    return
                raise
            if not lot:
                return
            yield from lot
            total = int((entetes or {}).get("x-wp-totalpages") or 0)
            if (total and page >= total) or (not total and len(lot) < par_page):
                return
            page += 1

    def page_publique(self, url: str) -> str:
        texte, _ = self.appel("GET", url, auth=False, entetes={"Accept": "text/html"})
        return texte if isinstance(texte, str) else ""


def identifiants() -> tuple[str, str, str]:
    """(site, utilisateur, mot de passe). Seuls les NOMS des variables manquantes sont cités."""
    charger_env()
    site = os.environ.get("WP_SITE_URL", "").strip()
    utilisateur = (os.environ.get("WP_USER") or os.environ.get("WP_USERNAME") or "").strip()
    mot_de_passe = os.environ.get("WP_APP_PASSWORD", "").strip()
    manquantes = [nom for nom, v in (("WP_SITE_URL", site), ("WP_USER", utilisateur),
                                     ("WP_APP_PASSWORD", mot_de_passe)) if not v]
    if manquantes:
        raise ErreurWP(f"Variables absentes : {', '.join(manquantes)}. Renseignez-les dans le .env du projet "
                       "(ou l'environnement de la routine). Le mot de passe se crée dans WordPress : "
                       "Utilisateurs → Profil → Mots de passe d'application.")
    if "votre-site" in site or not site.startswith(("http://", "https://")):
        raise ErreurWP("WP_SITE_URL doit être l'adresse complète du site, avec https:// (valeur d'exemple ou incomplète).")
    return site, utilisateur, mot_de_passe


def ouvrir_client(simuler: bool = False) -> ClientWP | None:
    try:
        return ClientWP(*identifiants())
    except ErreurWP:
        if simuler:
            print("  (simulation sans identifiants WordPress : aucune lecture du site)")
            return None
        raise


def plugin_seo(client: ClientWP | None, force: str | None) -> str | None:
    if force:
        return None if force == "aucun" else force
    if client is None:
        return None
    racine = client.get("/") or {}
    namespaces = racine.get("namespaces", []) if isinstance(racine, dict) else []
    trouves = [nom for nom, ns in NAMESPACES_SEO if ns in namespaces]
    if len(trouves) > 1:
        print(f"  ! Plusieurs extensions SEO actives ({', '.join(trouves)}) : {trouves[0]} retenue. "
              "Forcez avec --plugin-seo.")
    return detecter_plugin_seo(namespaces)


def base_rest(type_contenu: str) -> str:
    return {"post": "posts", "page": "pages"}.get(type_contenu, type_contenu)


def trouver(client: ClientWP, url: str | None = None, ident: int | None = None,
            type_contenu: str | None = None) -> tuple[dict, str]:
    """(élément en contexte edit, base REST). Par ID, ou par URL via le slug."""
    tous = "publish,draft,pending,future,private"
    if ident:
        bases = [base_rest(type_contenu)] if type_contenu else ["posts", "pages"]
        for base in bases:
            try:
                return client.get(f"/wp/v2/{base}/{ident}", context="edit"), base
            except ErreurWP:
                if base == bases[-1]:
                    raise
    if not url:
        raise ErreurWP("Précisez --url, ou --id (et --type).")
    slug = unquote(urlparse(url).path).rstrip("/").rsplit("/", 1)[-1]
    if not slug:
        raise ErreurWP("La page d'accueil n'a pas de slug : utilisez --id (Réglages → Lecture indique la page utilisée).")
    trouves = []
    for base in ([base_rest(type_contenu)] if type_contenu else ["pages", "posts"]):
        for item in client.get(f"/wp/v2/{base}", slug=slug, context="edit", status=tous) or []:
            trouves.append((item, base))
    exacts = [t for t in trouves if cle_url(t[0].get("link", "")) == cle_url(url)]
    if len(exacts) == 1 or (len(trouves) == 1 and not exacts):
        return (exacts or trouves)[0]
    if not trouves:
        raise ErreurWP(f"Aucun article ni page avec le slug « {slug} ». Vérifiez l'URL, ou utilisez --id.")
    raise ErreurWP(f"Plusieurs contenus répondent au slug « {slug} » : utilisez --id "
                   f"({', '.join(str(t[0].get('id')) for t in trouves)}).")


def verdict_garde_fou(action: str, cible: str) -> tuple[str, str]:
    import guard
    return guard.evaluer(action, cible, None)


def autoriser(action: str, cible: str, valide: bool, simuler: bool) -> bool:
    verdict, explication = verdict_garde_fou(action, cible)
    ok, message = decision_ecriture(verdict, valide)
    print(f"  Garde-fou ({action}) : {verdict} — {explication}")
    if not ok:
        print(f"  {'(simulation) ' if simuler else '✗ '}{message}")
    return ok


def sauvegarder(item: dict, type_rest: str, plugin: str | None) -> Path:
    maintenant = dt.datetime.now()
    dossier = dossier_etat("backups")
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / nom_sauvegarde(item, maintenant)
    chemin.write_text(json.dumps(donnees_sauvegarde(item, type_rest, plugin, maintenant),
                                 ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        affiche = chemin.relative_to(racine_projet())
    except ValueError:
        affiche = chemin
    print(f"  Sauvegarde : {affiche}  (retour arrière : cms_restore.py {chemin.name})")
    return chemin


def journaliser(cmd: list[str], simuler: bool) -> None:
    lisible = " ".join(f'"{c}"' if " " in c else c for c in ["journal.py", *cmd[2:]])
    if simuler:
        print(f"  (simulation) journal : {lisible}")
        return
    r = subprocess.run(cmd, capture_output=True, text=True)
    sortie = (r.stdout + r.stderr).strip()
    if sortie:
        print("  " + sortie.replace("\n", "\n  "))
    if r.returncode:
        print(f"  ! Journalisation échouée : relancez à la main → {lisible}")


def lien_edition(client: ClientWP, ident) -> str:
    return f"{client.site}/wp-admin/post.php?post={ident}&action=edit"


def ecrire_meta_rankmath(client: ClientWP, ident: int, meta: dict) -> bool:
    """Rank Math n'expose pas toujours ses champs dans `meta`, mais fournit sa
    propre route d'écriture. On la tente avant de conclure à un échec."""
    try:
        client.post("/rankmath/v1/updateMeta", {"objectType": "post", "objectID": ident, "meta": meta})
        return True
    except ErreurWP as exc:
        print(f"  ! Route Rank Math indisponible : {exc}")
        return False


def expliquer_meta_non_ecrite(plugin: str | None, manquants: list[str]) -> None:
    print(f"  ! Champs SEO non écrits ({', '.join(manquants)}) : ils ne sont pas exposés dans l'API REST.")
    print(f"    Solution : le mu-plugin {MU_PLUGIN_SEO}")
    print("    à déposer dans wp-content/mu-plugins/ (installation et test : templates/wordpress/README.md).")
    if plugin == "yoast":
        print("    Sans toucher au serveur : régler le modèle de meta description de Yoast sur %%excerpt%%")
        print("    puis relancer avec --via-extrait (le title reste alors le modèle Yoast).")


def controler(chemin: str) -> tuple[bool, str]:
    """controle_contenu.py, bloquant : une consigne s'oublie, un code retour non."""
    r = subprocess.run([sys.executable, str(SCRIPTS / "controle_contenu.py"), chemin],
                       capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def lire_html(chemin: str) -> str:
    fichier = Path(chemin)
    if not fichier.is_file():
        raise ErreurWP(f"Fichier introuvable : {chemin}")
    return fichier.read_text(encoding="utf-8")


def resoudre_termes(client: ClientWP | None, taxonomie: str, valeurs: str | None) -> list[int]:
    """IDs depuis des IDs ou des noms. Aucune création : l'arborescence est une décision humaine."""
    if not valeurs:
        return []
    ids = []
    for valeur in [v.strip() for v in valeurs.split(",") if v.strip()]:
        if valeur.isdigit():
            ids.append(int(valeur))
            continue
        if client is None:
            print(f"  (simulation) {taxonomie} « {valeur} » : résolue à l'exécution")
            continue
        termes = client.get(f"/wp/v2/{taxonomie}", search=valeur, per_page=100) or []
        exact = [t for t in termes if html_lib.unescape(t.get("name", "")).lower() == valeur.lower()
                 or t.get("slug") == slugifier(valeur)]
        if not exact:
            proches = ", ".join(html_lib.unescape(t.get("name", "")) for t in termes[:5]) or "aucune"
            raise ErreurWP(f"{taxonomie} « {valeur} » introuvable (proches : {proches}). Créez-la dans "
                           "WordPress ou passez son ID.")
        ids.append(exact[0]["id"])
    return ids


def televerser(client: ClientWP, fichier: Path, alt: str, titre: str | None = None,
               legende: str | None = None) -> dict:
    mime = mimetypes.guess_type(fichier.name)[0] or ""
    nom = slugifier(fichier.stem) + fichier.suffix.lower()
    # Création non idempotente : pas de nouvel essai automatique, sinon un
    # média en double à chaque coupure réseau.
    media, _ = client.appel("POST", "/wp/v2/media", corps=fichier.read_bytes(), reessayer=False,
                            entetes={"Content-Type": mime, "Content-Disposition": f'attachment; filename="{nom}"'})
    champs = {"alt_text": alt}
    if titre:
        champs["title"] = titre
    if legende:
        champs["caption"] = legende
    try:
        client.post(f"/wp/v2/media/{media['id']}", champs)
    except ErreurWP as exc:
        print(f"  ! Média {media['id']} téléversé, mais texte alternatif non enregistré : {exc}")
    return media


def verifier_image(chemin: str) -> Path:
    fichier = Path(chemin)
    if not fichier.is_file():
        raise ErreurWP(f"Image introuvable : {chemin}")
    mime = mimetypes.guess_type(fichier.name)[0] or ""
    if not mime.startswith("image/"):
        raise ErreurWP(f"{fichier.name} n'est pas une image reconnue.")
    poids = fichier.stat().st_size // 1024
    if poids > 300:
        print(f"  ! {fichier.name} pèse {poids} Ko : au-dessus de 300 Ko, elle pèse sur le LCP. "
              "Convertissez en WebP, 1600 px de large au plus.")
    return fichier


# ═══════════════════════════════════════════════════════════════════
# Commandes
# ═══════════════════════════════════════════════════════════════════

def cmd_verifier(a) -> int:
    client = ouvrir_client()
    moi = client.get("/wp/v2/users/me", context="edit")
    roles = ", ".join(moi.get("roles", [])) or "inconnu"
    print(f"\n  Site        : {client.site}")
    print(f"  Compte      : {moi.get('slug', '?')} ({roles})")
    droits = moi.get("capabilities", {}) or {}
    for droit, sens in (("edit_posts", "créer des articles"), ("publish_posts", "publier des articles"),
                        ("edit_pages", "modifier des pages"), ("edit_others_posts", "modifier les contenus des autres"),
                        ("upload_files", "téléverser des images")):
        print(f"  {'✓' if droits.get(droit) else '✗'} {sens}")
    plugin = plugin_seo(client, a.plugin_seo)
    print(f"  Extension SEO : {plugin or 'aucune détectée'}")
    if plugin in CHAMPS_SEO:
        exemple = client.get("/wp/v2/posts", per_page=1, context="edit", _fields="id,meta") or []
        meta = (exemple[0].get("meta") or {}) if exemple else {}
        exposes = [c for c in CHAMPS_SEO[plugin].values() if isinstance(meta, dict) and c in meta]
        if exposes:
            print(f"  ✓ Champs SEO exposés dans l'API : {', '.join(exposes)}")
        elif exemple:
            expliquer_meta_non_ecrite(plugin, list(CHAMPS_SEO[plugin].values()))
    verdict, explication = verdict_garde_fou("publier", client.site + "/")
    print(f"  Garde-fou   : {verdict} — {explication}")
    print(f"  Statut par défaut des contenus neufs : {statut_par_defaut()}\n")
    return 0


def statut_par_defaut() -> str:
    statut = lire_valeur("publication.statut_par_defaut", "draft")
    return statut if statut in STATUTS else "draft"


def cmd_publier(a) -> int:
    html = lire_html(a.html)
    conforme, rapport = controler(a.html)
    if not conforme:
        print("  " + rapport.replace("\n", "\n  "))
        if not a.simuler:
            raise ErreurWP("Contrôle qualité bloquant (controle_contenu.py) : corrigez le fichier avant de publier.")
    if not a.brut:
        html = durcir_html(html)
    if re.search(r"<h1[\s>]", html, re.I):
        print("  ! Le fichier contient un <h1> : le thème affiche déjà le titre en H1. Retirez-le du fichier.")
    if not a.id and not a.titre:
        raise ErreurWP("--titre est obligatoire pour un contenu neuf.")
    problemes = problemes_meta(a.meta_titre, a.meta_description)
    if problemes and not a.hors_format:
        raise ErreurWP("; ".join(problemes) + ". Corrigez, ou forcez avec --hors-format.")

    client = ouvrir_client(a.simuler)
    base = base_rest(a.type)
    existant = None
    if a.id:
        if client is None:
            raise ErreurWP("Mise à jour d'un contenu existant : les identifiants WordPress sont nécessaires, même en simulation.")
        existant, base = trouver(client, ident=a.id, type_contenu=a.type)
    slug = slugifier(a.slug or a.titre) if (a.slug or not existant) else None
    if client and not existant and slug:
        doublons = client.get(f"/wp/v2/{base}", slug=slug, context="edit",
                              status="publish,draft,pending,future,private") or []
        if doublons:
            d = doublons[0]
            raise ErreurWP(f"Un contenu existe déjà avec le slug « {slug} » (ID {d['id']}, {d.get('status')}). "
                           f"Pour le mettre à jour : --id {d['id']}. Pour un autre contenu : un autre --slug.")

    statut_demande = a.statut or (None if existant else statut_par_defaut())
    mode = mode_ecriture(existant.get("status") if existant else None, statut_demande)
    plugin = plugin_seo(client, a.plugin_seo)
    extrait = a.extrait
    if a.via_extrait and a.meta_description:
        extrait = a.meta_description
    meta = {} if a.via_extrait else charge_meta_seo(plugin, a.meta_titre, a.meta_description)
    if (a.meta_titre or a.meta_description) and not meta and not a.via_extrait:
        print("  ! Aucune extension SEO détectée : title et meta description ne seront pas écrits "
              "(--plugin-seo pour forcer, --via-extrait si le thème sert l'extrait en meta description).")
    categories = resoudre_termes(client, "categories", a.categories or (
        lire_valeur("publication.categorie_par_defaut") if base == "posts" and not existant else None))
    etiquettes = resoudre_termes(client, "tags", a.etiquettes)
    image_id = int(a.image_une) if a.image_une and a.image_une.isdigit() else None
    image_fichier = None
    if a.image_une and image_id is None:
        image_fichier = verifier_image(a.image_une)
        if not a.alt_image:
            raise ErreurWP("--alt-image est obligatoire avec une image à téléverser : une image sans alt "
                           "ne sert ni l'accessibilité ni la recherche d'images.")

    cible = (existant or {}).get("link") or f"{client.site if client else ''}/{slug or ''}/"
    action = "mettre-a-jour-page" if existant else "publier"
    libelles = {"creation": f"création en « {statut_demande} »", "brouillon": "mise à jour du brouillon",
                "revision": "révision proposée (autosave) — la page en ligne ne change pas",
                "en-ligne": "mise à jour EN LIGNE"}
    print(f"\n  {a.type} · {libelles[mode]}")
    print(f"  Titre   : {a.titre or texte_brut(_champ_rendu(existant.get('title')))}")
    if slug:
        print(f"  Slug    : {slug}")
    print(f"  Contenu : {len(html)} caractères, {analyser_contenu(html, cible)['nb_mots']} mots")
    if meta:
        print(f"  SEO ({plugin}) : " + " · ".join(f"{k} = {v}" for k, v in meta.items()))
    if extrait:
        print(f"  Extrait : {extrait}")
    if mode == "revision" and (meta or categories or etiquettes or a.image_une or a.slug):
        print("  ! En révision, seuls titre, contenu et extrait sont proposés. Meta, catégories, image et slug")
        print("    changeraient la page en ligne : ils ne sont pas envoyés (relancez après validation).")

    ok = autoriser(action, cible, a.valide, a.simuler)
    if a.simuler:
        print("\n  Simulation : rien n'a été écrit.\n")
        return 0
    if not ok:
        return 2

    if image_fichier is not None:
        media = televerser(client, image_fichier, a.alt_image)
        image_id = media["id"]
        print(f"  Image à la une : média {image_id}")

    sauvegarde = sauvegarder(existant, base, plugin) if existant else None
    if mode == "revision":
        charge = {"title": a.titre or _champ_brut(existant.get("title")), "content": html,
                  "excerpt": extrait if extrait is not None else _champ_brut(existant.get("excerpt"))}
        reponse = client.post(f"/wp/v2/{base}/{existant['id']}/autosaves", charge)
        print(f"\n  ✓ Révision proposée pour {existant.get('link')}")
        print(f"    À relire et valider dans l'éditeur : {lien_edition(client, existant['id'])}")
        print("    (bandeau « Il existe une sauvegarde automatique plus récente » → la restaurer, puis Mettre à jour)\n")
        return 0

    charge = construire_charge(titre=a.titre, html=html, statut=statut_demande, slug=slug, extrait=extrait,
                               categories=categories, etiquettes=etiquettes, image_une=image_id, meta=meta)
    if existant:
        reponse = client.post(f"/wp/v2/{base}/{existant['id']}", charge)
    else:
        try:
            reponse = client.post(f"/wp/v2/{base}", charge, reessayer=False)
        except ErreurConnexion:
            # La connexion a pu couper après la création : on vérifie avant de
            # conclure, plutôt que de relancer et créer un doublon.
            deja = client.get(f"/wp/v2/{base}", slug=slug, context="edit", status="publish,draft,pending,future,private")
            if not deja:
                raise
            reponse = deja[0]
            print("  (connexion coupée, mais le contenu a bien été créé)")
    manquants = meta_non_ecrits(reponse, meta) if meta else []
    if manquants and plugin == "rankmath" and ecrire_meta_rankmath(client, reponse["id"], meta):
        manquants = []
    if manquants:
        expliquer_meta_non_ecrite(plugin, manquants)

    statut_final = reponse.get("status")
    print(f"\n  ✓ {a.type} {reponse.get('id')} · statut {statut_final}")
    print(f"    Lien    : {reponse.get('link')}")
    print(f"    Éditer  : {lien_edition(client, reponse.get('id'))}")
    if statut_final != "publish":
        print(f"    Aperçu  : {client.site}/?p={reponse.get('id')}&preview=true")
    if statut_final == "publish":
        titre = a.titre or texte_brut(_champ_rendu(reponse.get("title")))
        if existant and existant.get("status") == "publish":
            journaliser(commande_journal(reponse["link"], "contenu", f"sauvegarde {sauvegarde.name}",
                                         f"contenu republié depuis {Path(a.html).name}", a.requete, a.auto), False)
        else:
            journaliser(commande_journal(reponse["link"], "page-neuve", "", titre, a.requete, a.auto), False)
    else:
        print("    Journal : la page sera journalisée (type page-neuve) le jour de sa mise en ligne.")
    print()
    return 0


def cmd_media(a) -> int:
    fichier = verifier_image(a.fichier)
    if not a.alt.strip():
        raise ErreurWP("--alt ne peut pas être vide.")
    client = ouvrir_client(a.simuler)
    print(f"\n  Média : {fichier.name} ({fichier.stat().st_size // 1024} Ko) · alt « {a.alt} »")
    cible = (client.site if client else "") + "/"
    ok = autoriser("publier", cible, a.valide, a.simuler)
    if a.simuler:
        print("\n  Simulation : rien n'a été téléversé.\n")
        return 0
    if not ok:
        return 2
    media = televerser(client, fichier, a.alt, a.titre, a.legende)
    print(f"  ✓ Média {media.get('id')} téléversé")
    print(f"MEDIA_ID={media.get('id')}")
    print(f"SOURCE_URL={media.get('source_url')}")
    return 0


def cmd_meta(a) -> int:
    if a.titre_seo is None and a.description is None:
        raise ErreurWP("Rien à changer : précisez --titre-seo et/ou --description.")
    problemes = problemes_meta(a.titre_seo, a.description)
    if problemes and not a.hors_format:
        raise ErreurWP("; ".join(problemes) + ". Corrigez, ou forcez avec --hors-format.")
    client = ouvrir_client()
    item, base = trouver(client, a.url, a.id, a.type)
    plugin = plugin_seo(client, a.plugin_seo)
    url = item.get("link") or a.url
    if a.via_extrait and a.titre_seo is not None:
        raise ErreurWP("--via-extrait ne concerne que la meta description : le title passe par l'extension SEO.")
    if plugin is None and not a.via_extrait:
        raise ErreurWP("Aucune extension SEO détectée : le title vient du thème. Pour la meta description, "
                       "--via-extrait si le thème ou l'extension sert l'extrait. Sinon --plugin-seo.")

    # La valeur d'avant, telle que servie : c'est elle que le journal compare.
    titre_avant, desc_avant = lire_seo_affiche(item)
    if not (titre_avant or desc_avant) and item.get("status") == "publish":
        try:
            tete = extraire_head(client.page_publique(url))
            titre_avant, desc_avant = tete["title"], tete["description"]
        except ErreurWP as exc:
            print(f"  ! Page publique illisible ({exc}) : valeur d'avant lue dans les champs bruts.")
    champs = lire_seo_champs(item, plugin)
    if plugin in CHAMPS_SEO:
        titre_avant = titre_avant or champs.get(CHAMPS_SEO[plugin]["titre"], "")
        desc_avant = desc_avant or champs.get(CHAMPS_SEO[plugin]["description"], "")
    if a.via_extrait:
        desc_avant = texte_brut(_champ_brut(item.get("excerpt"))) or desc_avant

    changements = []
    if a.titre_seo is not None and a.titre_seo != titre_avant:
        changements.append(("title", titre_avant, a.titre_seo))
    if a.description is not None and a.description != desc_avant:
        changements.append(("meta", desc_avant, a.description))
    print(f"\n  {url}  ({base} {item.get('id')}, {item.get('status')}, extension : {plugin or 'extrait'})")
    if not changements:
        print("  Déjà à jour, rien à écrire.\n")
        return 0
    for type_modif, avant, apres in changements:
        print(f"  {type_modif:<6} avant : {avant or '(vide — modèle de l’extension)'}")
        print(f"  {'':<6} après : {apres}  ({len(apres)} car.)")

    ok = autoriser("mettre-a-jour-page", url, a.valide, a.simuler)
    en_ligne = item.get("status") == "publish"
    if a.simuler:
        if en_ligne:
            for type_modif, avant, apres in changements:
                journaliser(commande_journal(url, type_modif, avant, apres, a.requete, a.auto), True)
        print("\n  Simulation : rien n'a été écrit.\n")
        return 0
    if not ok:
        return 2

    sauvegarder(item, base, plugin)
    if a.via_extrait:
        client.post(f"/wp/v2/{base}/{item['id']}", {"excerpt": a.description})
    else:
        meta = charge_meta_seo(plugin, a.titre_seo, a.description)
        reponse = client.post(f"/wp/v2/{base}/{item['id']}", {"meta": meta})
        manquants = meta_non_ecrits(reponse, meta)
        if manquants and plugin == "rankmath" and ecrire_meta_rankmath(client, item["id"], meta):
            manquants = []
        if manquants:
            expliquer_meta_non_ecrite(plugin, manquants)
            return 1
    print("  ✓ Écrit.")
    if en_ligne:
        note = "title et meta changés ensemble" if len(changements) == 2 else None
        for type_modif, avant, apres in changements:
            journaliser(commande_journal(url, type_modif, avant, apres, a.requete, a.auto, note), False)
    else:
        print("  Contenu non publié : rien à journaliser avant sa mise en ligne.")
    print()
    return 0


def chemin_projet(chemin: str) -> Path:
    p = Path(chemin)
    return p if p.is_absolute() else racine_projet() / p


def ecrire_carte(lignes: list[dict], chemin: Path) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES_CARTE, extrasaction="ignore")
        w.writeheader()
        w.writerows(lignes)


def lire_carte(chemin: Path) -> list[dict]:
    if not chemin.is_file():
        raise ErreurWP(f"Carte introuvable ({chemin}). Lancez d'abord : wp.py carte")
    with open(chemin, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def cmd_carte(a) -> int:
    client = ouvrir_client()
    plugin = plugin_seo(client, a.plugin_seo)
    lignes = []
    for base in [t.strip() for t in a.types.split(",") if t.strip()]:
        champs = "id,link,slug,type,status,title,content,modified,yoast_head_json,meta"
        for item in client.lister(f"/wp/v2/{base}", {"status": a.statut, "_fields": champs}):
            lignes.append(ligne_carte(item, client.site, base, plugin))
        print(f"  {base} : {sum(1 for l in lignes if l['type'] == base)} contenu(s)")
    if a.head:
        # Sans Yoast, l'API ne dit pas quel title est servi : on le lit sur la page.
        for ligne in lignes:
            if ligne["statut"] != "publish" or (ligne["meta_titre"] and ligne["meta_description"]):
                continue
            try:
                tete = extraire_head(client.page_publique(ligne["url"]))
                ligne["meta_titre"] = ligne["meta_titre"] or tete["title"]
                ligne["meta_description"] = ligne["meta_description"] or tete["description"]
            except ErreurWP as exc:
                print(f"  ! {ligne['url']} : {exc}")
            time.sleep(a.delai)
    calculer_entrants(lignes)
    sortie = chemin_projet(a.sortie)
    ecrire_carte(lignes, sortie)
    print(f"\n  ✓ {len(lignes)} contenus → {sortie}")

    orphelines = sorted((l for l in lignes if l["liens_entrants"] == 0), key=lambda l: -l["nb_mots"])
    impasses = [l for l in lignes if l["nb_liens_internes"] == 0]
    sans_meta = [l for l in lignes if not l["meta_description"]]
    print(f"  {len(orphelines)} orpheline(s) (aucun lien depuis le corps d'une autre page), "
          f"{len(impasses)} impasse(s) (aucun lien interne sortant), {len(sans_meta)} sans meta description lue.")
    for l in orphelines[:10]:
        print(f"    · orpheline : {l['url']}  ({l['nb_mots']} mots)")
    doublons = doublons_potentiels(lignes)
    if doublons:
        print(f"\n  {len(doublons)} paire(s) au sujet très proche — cannibalisation possible, à croiser avec")
        print("  Search Console (deux URL qui alternent sur la même requête) :")
        for r, x, y in doublons[:10]:
            print(f"    · {r:.2f}  {x['url']}  ↔  {y['url']}")
    print("\n  Suite : wp.py maillage (liens à poser), gsc_analyse.py pour confirmer une cannibalisation.\n")
    return 0


def brouillon_depuis_html(html: str, titre: str | None, site: str) -> dict:
    analyse = analyser_contenu(html, site)
    titre = titre or (analyse["h1"][0] if analyse["h1"] else extraire_head(html)["title"])
    if not titre:
        raise ErreurWP("Titre introuvable dans le fichier : précisez --titre.")
    return {"url": "", "titre": titre, "meta_titre": "", "meta_description": "", "h1": "",
            "h2": " | ".join(analyse["h2"]), "termes": " ".join(analyse["termes"]),
            "liens_internes": analyse["liens_internes"]}


def cmd_maillage(a) -> int:
    lignes = lire_carte(chemin_projet(a.carte))
    site = urlparse(lignes[0]["url"]).scheme + "://" + urlparse(lignes[0]["url"]).netloc if lignes else ""

    if a.html:
        html = lire_html(a.html)
        brouillon = brouillon_depuis_html(html, a.titre, site)
        touches = cannibalisation(brouillon, lignes)
        if touches:
            print("\n  ! Ces pages couvrent déjà ce sujet — optimiser l'existante vaut souvent mieux qu'en créer une :")
            for r, l in touches[:5]:
                print(f"    · {r:.2f}  {l['url']}  « {l['titre']} »")
        sortants = suggerer_sortants(brouillon, lignes, a.max, a.seuil)
        print(f"\n  {len(sortants)} lien(s) sortant(s) suggéré(s) pour « {brouillon['titre']} » :")
        places = 0
        for s in sortants:
            etat = ""
            if a.appliquer:
                html, ancre = inserer_lien(html, ancres_candidates(next(l for l in lignes if l["url"] == s["cible"])),
                                           s["cible"])
                etat = f" → posé sur « {ancre} »" if ancre else " → ancre absente du texte, à placer à la main"
                places += bool(ancre)
            print(f"    · {s['score']:.2f}  {s['cible']}  ancre : « {s['ancre']} »{etat}")
        if a.appliquer and places and not a.simuler:
            Path(a.html).write_text(html, encoding="utf-8")
            print(f"\n  ✓ {places} lien(s) posé(s) dans {a.html} (fichier local, rien n'est envoyé au site).")
        print()
        return 0

    suggestions = suggerer_liens(lignes, a.cible, a.max, a.seuil, a.entrants_max)
    if a.cible and not any(cle_url(l["url"]) == cle_url(a.cible) for l in lignes):
        raise ErreurWP("Cible absente de la carte : relancez wp.py carte si elle est récente.")
    if not suggestions:
        print("\n  Aucun lien pertinent à suggérer (baissez --seuil pour élargir).\n")
        return 0
    print(f"\n  {len(suggestions)} lien(s) entrant(s) suggéré(s) :")
    for s in suggestions:
        print(f"    · {s['score']:.2f}  {s['source']}\n           → {s['cible']}  ancre : « {s['ancre']} »"
              f"  (communs : {s['mots_communs']})")
    if a.sortie:
        chemin = chemin_projet(a.sortie)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        with open(chemin, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(suggestions[0]))
            w.writeheader()
            w.writerows(suggestions)
        print(f"  → {chemin}")
    if not a.appliquer:
        print("\n  Pour les poser (brouillon ou révision, jamais en direct) : --appliquer [--simuler]\n")
        return 0
    return appliquer_maillage(a, suggestions, lignes)


def appliquer_maillage(a, suggestions: list[dict], lignes: list[dict]) -> int:
    """Pose les liens dans les pages sources. Une page en ligne reçoit une
    révision (autosave) à valider : le maillage ne part jamais en direct seul."""
    client = ouvrir_client()
    plugin = None
    faits = manuels = 0
    ancres_par_cible = {l["url"]: ancres_candidates(l) for l in lignes}
    for s in suggestions[:a.max_modifs]:
        item, base = trouver(client, ident=int(s["source_id"]), type_contenu=s["source_type"] or None)
        contenu = _champ_brut(item.get("content"))
        if deja_lie(contenu, s["cible"], client.site):
            print(f"  = {s['source']} lie déjà {s['cible']}")
            continue
        nouveau, ancre = inserer_lien(contenu, ancres_par_cible.get(s["cible"], [s["ancre"]]), s["cible"])
        if not ancre:
            manuels += 1
            print(f"  ✎ {s['source']} : aucune ancre dans le texte → à placer à la main vers {s['cible']}")
            continue
        mode = mode_ecriture(item.get("status"), None)
        print(f"  → {s['source']} : « {ancre} » → {s['cible']}  ({'révision' if mode == 'revision' else 'brouillon'})")
        if not autoriser("mettre-a-jour-page", item.get("link") or s["source"], a.valide, a.simuler):
            if a.simuler:
                continue
            return 2
        if a.simuler:
            continue
        sauvegarder(item, base, plugin)
        if mode == "revision":
            client.post(f"/wp/v2/{base}/{item['id']}/autosaves",
                        {"title": _champ_brut(item.get("title")), "content": nouveau,
                         "excerpt": _champ_brut(item.get("excerpt"))})
        else:
            client.post(f"/wp/v2/{base}/{item['id']}", {"content": nouveau})
        faits += 1
    print(f"\n  {faits} lien(s) posé(s), {manuels} à placer à la main."
          + (" Simulation : rien n'a été écrit." if a.simuler else ""))
    if faits:
        print("  Les révisions se valident dans l'éditeur de chaque page. Une fois en ligne, journalisez :")
        print("  journal.py ajouter --url <page liée> --type maillage --avant \"<n> liens entrants\" --apres \"<n+1>\"")
    print()
    return 0


def cmd_remplacer(a) -> int:
    """Remplace un bloc identifié par un motif dans tous les contenus.

    Un bloc répété dans des pages déjà publiées (encart, bandeau, CSS inline)
    ne change pas quand on corrige sa source : il faut le repousser page par
    page. Une page où le motif apparaît plusieurs fois est ignorée — on ne
    devine pas lequel remplacer.
    """
    try:
        motif = re.compile(a.motif, re.S)
    except re.error as exc:
        raise ErreurWP(f"Motif invalide : {exc}") from None
    remplacement = lire_html(a.par_fichier) if a.par_fichier else (a.par or "")
    if not a.brut:
        remplacement = durcir_html(remplacement)
    client = ouvrir_client()
    exclus = {s.strip() for s in (a.exclure or "").split(",") if s.strip()}
    faits = identiques = 0
    for base in [t.strip() for t in a.types.split(",") if t.strip()]:
        for item in client.lister(f"/wp/v2/{base}", {"status": a.statut, "context": "edit"}):
            if item.get("slug") in exclus:
                continue
            contenu = _champ_brut(item.get("content"))
            trouves = len(motif.findall(contenu))
            if trouves == 0:
                continue
            if trouves > 1:
                print(f"  ? {item.get('link')} : {trouves} occurrences, page ignorée")
                continue
            nouveau = motif.sub(lambda _: remplacement, contenu)
            if nouveau == contenu:
                identiques += 1
                continue
            if faits >= a.max_modifs:
                print(f"  … limite de {a.max_modifs} modification(s) atteinte (--max-modifs)")
                break
            mode = mode_ecriture(item.get("status"), "publish" if a.en_ligne else None)
            libelle = {"revision": "révision", "en-ligne": "EN LIGNE"}.get(mode, "brouillon")
            print(f"  ~ {item.get('link')}  ({libelle})")
            if not autoriser("mettre-a-jour-page", item.get("link", ""), a.valide, a.simuler):
                if a.simuler:
                    continue
                return 2
            if a.simuler:
                faits += 1
                continue
            sauvegarde = sauvegarder(item, base, None)
            if mode == "revision":
                client.post(f"/wp/v2/{base}/{item['id']}/autosaves",
                            {"title": _champ_brut(item.get("title")), "content": nouveau,
                             "excerpt": _champ_brut(item.get("excerpt"))})
            else:
                client.post(f"/wp/v2/{base}/{item['id']}", {"content": nouveau})
                if mode == "en-ligne":
                    journaliser(commande_journal(item["link"], a.type_journal, f"sauvegarde {sauvegarde.name}",
                                                 f"bloc remplacé ({a.motif[:40]})"), False)
            faits += 1
    print(f"\n  {faits} contenu(s) {'à modifier' if a.simuler else 'modifié(s)'}, {identiques} déjà à jour."
          + (" Simulation : rien n'a été écrit." if a.simuler else "") + "\n")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="WordPress par l'API REST — brouillon par défaut, garde-fou, journal")
    sp = p.add_subparsers(dest="commande", required=True)

    def ecriture(sous):
        sous.add_argument("--simuler", action="store_true", help="n'écrit rien, affiche le plan")
        sous.add_argument("--valide", action="store_true",
                          help="validation humaine obtenue (uniquement après un oui explicite)")

    def seo(sous):
        sous.add_argument("--plugin-seo", choices=["yoast", "rankmath", "seopress", "aucun"],
                          help="forcer l'extension SEO au lieu de la détecter")

    v = sp.add_parser("verifier", help="identifiants, droits, extension SEO, garde-fou")
    seo(v)

    pb = sp.add_parser("publier", help="créer ou mettre à jour un article ou une page")
    pb.add_argument("--html", required=True, help="fichier HTML du contenu (sans <h1>)")
    pb.add_argument("--titre")
    pb.add_argument("--slug")
    pb.add_argument("--extrait")
    pb.add_argument("--type", choices=["post", "page"], default="post")
    pb.add_argument("--id", type=int, help="contenu existant à mettre à jour")
    pb.add_argument("--statut", choices=STATUTS, help="défaut : publication.statut_par_defaut (draft)")
    pb.add_argument("--categories", help="noms ou IDs, séparés par des virgules")
    pb.add_argument("--etiquettes", help="noms ou IDs, séparés par des virgules")
    pb.add_argument("--image-une", help="ID de média ou fichier image à téléverser")
    pb.add_argument("--alt-image", help="texte alternatif de l'image à la une")
    pb.add_argument("--meta-titre")
    pb.add_argument("--meta-description")
    pb.add_argument("--via-extrait", action="store_true", help="meta description écrite dans l'extrait")
    pb.add_argument("--hors-format", action="store_true", help="accepter une meta hors zone 120-156")
    pb.add_argument("--brut", action="store_true", help="ne pas protéger <style>/<script> contre wpautop")
    pb.add_argument("--requete", help="requête visée, pour le journal")
    pb.add_argument("--auto", action="store_true", help="journal : situation de départ relevée dans Search Console")
    ecriture(pb)
    seo(pb)

    md = sp.add_parser("media", help="téléverser une image avec son texte alternatif")
    md.add_argument("--fichier", required=True)
    md.add_argument("--alt", required=True)
    md.add_argument("--titre")
    md.add_argument("--legende")
    ecriture(md)

    mt = sp.add_parser("meta", help="changer title et meta description d'un contenu existant")
    mt.add_argument("--url")
    mt.add_argument("--id", type=int)
    mt.add_argument("--type", choices=["post", "page"])
    mt.add_argument("--titre-seo")
    mt.add_argument("--description")
    mt.add_argument("--via-extrait", action="store_true",
                    help="écrire la description dans l'extrait (modèle Yoast réglé sur %%%%excerpt%%%%)")
    mt.add_argument("--hors-format", action="store_true")
    mt.add_argument("--requete", help="requête visée, pour le journal")
    mt.add_argument("--auto", action="store_true", help="journal : situation de départ relevée dans Search Console")
    ecriture(mt)
    seo(mt)

    ct = sp.add_parser("carte", help="carte de contenu → donnees/carte-contenu.csv")
    ct.add_argument("--types", default="posts,pages", help="bases REST, séparées par des virgules")
    ct.add_argument("--statut", default="publish")
    ct.add_argument("--sortie", default="donnees/carte-contenu.csv")
    ct.add_argument("--head", action="store_true", help="lire title et meta sur les pages publiques si l'API ne les donne pas")
    ct.add_argument("--delai", type=float, default=0.5, help="secondes entre deux pages avec --head")
    seo(ct)

    ml = sp.add_parser("maillage", help="liens internes à poser, depuis la carte")
    ml.add_argument("--carte", default="donnees/carte-contenu.csv")
    ml.add_argument("--cible", help="URL qui doit recevoir des liens")
    ml.add_argument("--html", help="nouveau contenu local : liens sortants et risque de cannibalisation")
    ml.add_argument("--titre", help="titre du nouveau contenu, si le fichier n'a pas de <h1>")
    ml.add_argument("--max", type=int, default=5, help="suggestions par cible")
    ml.add_argument("--seuil", type=float, default=0.5, help="pertinence minimale, 0 à 1")
    ml.add_argument("--entrants-max", type=int, default=1, help="sans --cible : pages qui reçoivent au plus N liens")
    ml.add_argument("--sortie", help="CSV des suggestions")
    ml.add_argument("--appliquer", action="store_true", help="poser les liens (brouillon ou révision uniquement)")
    ml.add_argument("--max-modifs", type=int, default=10)
    ecriture(ml)

    rp = sp.add_parser("remplacer", help="remplacer un bloc dans tous les contenus")
    rp.add_argument("--motif", required=True, help="expression régulière du bloc (une seule occurrence par page)")
    rp.add_argument("--par", help="texte de remplacement")
    rp.add_argument("--par-fichier", help="fichier HTML de remplacement")
    rp.add_argument("--types", default="pages,posts")
    rp.add_argument("--statut", default="publish")
    rp.add_argument("--exclure", help="slugs à ignorer, séparés par des virgules")
    rp.add_argument("--en-ligne", action="store_true", help="modifier les pages publiées en direct (garde-fou)")
    rp.add_argument("--max-modifs", type=int, default=50)
    rp.add_argument("--brut", action="store_true")
    rp.add_argument("--type-journal", default="contenu", choices=["contenu", "technique", "schema", "faq"])
    ecriture(rp)

    a = p.parse_args()
    commandes = {"verifier": cmd_verifier, "publier": cmd_publier, "media": cmd_media, "meta": cmd_meta,
                 "carte": cmd_carte, "maillage": cmd_maillage, "remplacer": cmd_remplacer}
    try:
        return commandes[a.commande](a)
    except ErreurWP as exc:
        print(f"\n  ✗ {exc}\n", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
