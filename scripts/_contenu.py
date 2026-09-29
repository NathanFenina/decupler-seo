"""Lire une page comme un rédacteur la lit — sans dépendance.

Brique commune de `serp_concurrents.py` et `style_maison.py` :

- `lire_html` / `lire_markdown` : isolent le contenu principal (sans menu,
  pied de page, barre latérale ni bandeau cookies) et en rendent le plan Hn,
  les listes, les tableaux, les images, les liens, la FAQ, les schémas, les
  dates, les paragraphes et une version Markdown qui garde la structure
  (titres et listes), prête à être lue ;
- les mesures de texte : mots, phrases, syllabes, lisibilité, adresse au
  lecteur (vous / tu), personne (nous / je), termes et expressions ;
- `telecharger` : urllib, agent identifié, délai court, adresses internes
  refusées.

Toutes les fonctions de calcul sont pures : les tests les exercent sur des
fragments HTML écrits à la main, sans réseau.
"""

from __future__ import annotations

import ipaddress
import json
import math
import re
import socket
import unicodedata
import urllib.error
import urllib.request
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

AGENT = "Mozilla/5.0 (compatible; ClaudeCodeSEODecupler/3.3; +https://decupler.com)"
TAILLE_MAX = 5 * 1024 * 1024

# ─── Texte ────────────────────────────────────────────────────────

MOTS_VIDES = set("""
a ai as au aux avec avez avoir avons ayant c ca car ce ceci cela celle celles celui ces cet cette
chaque chez ci comme comment d dans de des deja donc dont du elle elles en encore entre est et etaient
etait etant ete etre eu eux fait faire faut fois font hors il ils j je jusqu l la le les leur leurs lui
m ma mais me meme memes mes moi moins mon n ne ni non nos notre nous on ont ou par parce pas peu peut
peuvent plus pour pourquoi quand que quel quelle quelles quels qui quoi s sa sans se ses si sera seront
ses soit son sont sous sur t ta te tes toi ton tous tout toute toutes tres tu un une unes uns vers via voici
voila vos votre vous y ici aussi alors ainsi apres avant bien autre autres cas lors selon tant quelques
plusieurs doit doivent sera etc combien cet ceux dit elle leurs lorsque puis puisque celles chacun
the of and to in on for is are be with by an or as at from this that it its your you we our not can
""".split())

_MOT = re.compile(r"[^\W_]+(?:['’-][^\W_]+)*")
_JETON = re.compile(r"[^\W_]+(?:-[^\W_]+)*")


def sans_accents(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte.lower().replace("’", "'"))
                   if unicodedata.category(c) != "Mn")


def compter_mots(texte: str) -> int:
    """Un mot = une suite de lettres ou de chiffres ; « l'entreprise » compte pour un."""
    return len(_MOT.findall(texte or ""))


def jetons(texte: str) -> list[tuple[str, str]]:
    """(forme normalisée sans accents, forme affichable en minuscules)."""
    return [(sans_accents(m), m) for m in _JETON.findall((texte or "").lower().replace("’", "'"))]


def radical(mot: str) -> str:
    """Radical grossier : « installation », « installer » et « installateur » se rejoignent."""
    mot = mot[:-1] if len(mot) > 3 and mot[-1] in "sx" else mot
    return mot[:6]


def radicaux_utiles(texte: str, exclure: set[str] | None = None) -> set[str]:
    exclure = exclure or set()
    return {radical(n) for n, _ in jetons(texte) if n not in MOTS_VIDES and len(n) > 1} - exclure


def decouper_phrases(texte: str) -> list[str]:
    morceaux = re.split(r"(?<=[.!?…])[\"»”)]*\s+(?=[\"«“(]?[A-ZÀ-ÖØ-Þ0-9])", (texte or "").strip())
    return [m.strip() for m in morceaux if compter_mots(m) > 0]


_VOYELLES = re.compile(r"[aeiouyàâäéèêëîïôöùûüœæ]+")


def syllabes(mot: str) -> int:
    """Approximation française : groupes de voyelles, « e » muet final retiré."""
    m = mot.lower()
    n = len(_VOYELLES.findall(m))
    if n > 1 and re.search(r"[^aeiouyàâäéèêëîïôöùûü](?:e|es)$", m):
        n -= 1
    return max(1, n)


def lisibilite(textes: list[str]) -> float | None:
    """Indice de Kandel et Moles (Flesch adapté au français), indicatif.

    ≥ 70 facile · 50-70 courant · 30-50 exigeant · < 30 difficile.
    """
    phrases = [p for t in textes for p in decouper_phrases(t)]
    mots = [m for p in phrases for m in _MOT.findall(p)]
    if len(phrases) < 3 or len(mots) < 30:
        return None
    syl = sum(syllabes(m) for m in mots)
    return round(207 - 1.015 * (len(mots) / len(phrases)) - 73.6 * (syl / len(mots)), 1)


_VOUS = re.compile(r"(?<!rendez-)\b(?:vous|votre|vos)\b")
_TU = re.compile(r"\b(?:tu|toi|t'|te)\b|\b\w+-(?:toi|tu)\b")
_NOUS = re.compile(r"\b(?:nous|notre|nos)\b")
_JE = re.compile(r"\b(?:je|moi|mon|ma|mes|me)\b|\b[jm]'")


def pour_mille(n: int, total: int) -> float:
    return round(n * 1000 / total, 1) if total else 0.0


def adresse_et_personne(texte: str) -> dict:
    """Comment le texte parle au lecteur et d'où il parle, pour 1 000 mots.

    « nous » est compté hors « vous » ; un « nous » de politesse reste rare.
    """
    t = sans_accents(texte)
    total = compter_mots(texte)
    vous, tu = len(_VOUS.findall(t)), len(_TU.findall(t))
    nous, je = len(_NOUS.findall(t)), len(_JE.findall(t))
    return {"vous": pour_mille(vous, total), "tu": pour_mille(tu, total),
            "nous": pour_mille(nous, total), "je": pour_mille(je, total),
            "adresse": ("vouvoiement" if vous >= 2 * max(tu, 1) and vous * 1000 >= 2 * total
                        else "tutoiement" if tu >= 2 * max(vous, 1) and tu * 1000 >= 2 * total
                        else "impersonnel" if vous + tu == 0 else "mixte"),
            "personne": ("nous" if nous > je and nous * 1000 >= 2 * total
                         else "je" if je > nous and je * 1000 >= 2 * total else "impersonnel")}


def mesures_ton(page: dict) -> dict:
    """Le ton mesurable d'une page : adresse, personne, rythme."""
    texte = page.get("texte") or ""
    blocs = page.get("paragraphes") or texte.splitlines()
    phrases = [p for b in blocs for p in decouper_phrases(b)]
    longueurs = [compter_mots(p) for p in phrases]
    d = adresse_et_personne(texte)
    d["phrase_moyenne"] = round(sum(longueurs) / len(longueurs), 1) if longueurs else None
    d["questions_pct"] = round(sum(1 for p in phrases if p.rstrip().endswith("?")) * 100 / len(phrases), 1) \
        if phrases else None
    d["lisibilite"] = lisibilite(page.get("paragraphes") or [texte])
    return d


def termes(texte: str) -> tuple[Counter, dict]:
    """Mots (4 lettres et plus) et expressions de deux mots, hors mots vides et nombres.

    Renvoie (compteur par forme normalisée, forme affichable la plus fréquente).
    """
    compte, formes = Counter(), {}
    vus: dict[str, Counter] = {}
    j = jetons(texte)

    def noter(cle, forme):
        compte[cle] += 1
        vus.setdefault(cle, Counter())[forme] += 1

    for i, (n, f) in enumerate(j):
        if n in MOTS_VIDES or n.isdigit():
            continue
        if len(n) >= 4:
            noter(n, f)
        if i + 1 < len(j):
            n2, f2 = j[i + 1]
            if n2 not in MOTS_VIDES and not n2.isdigit() and len(n) >= 3 and len(n2) >= 3:
                noter(f"{n} {n2}", f"{f} {f2}")
    for cle, c in vus.items():
        formes[cle] = c.most_common(1)[0][0]
    return compte, formes


def ngrammes_recurrents(textes: list[str], tailles=(3, 4, 5), mini_docs: int = 2, maxi: int = 15) -> list[dict]:
    """Expressions de 3 à 5 mots qui reviennent d'un texte à l'autre : les tics de la maison."""
    par_doc: list[Counter] = []
    formes: dict[str, str] = {}
    for t in textes:
        c = Counter()
        for bloc in re.split(r"[.!?…:;\n]+", t):
            j = jetons(bloc)
            for k in tailles:
                for i in range(len(j) - k + 1):
                    fen = j[i:i + k]
                    normes = [n for n, _ in fen]
                    utiles = [n for n in normes if n not in MOTS_VIDES and not n.isdigit()]
                    if len(utiles) < 2 or normes[0] in MOTS_VIDES or normes[-1] in MOTS_VIDES:
                        continue
                    cle = " ".join(normes)
                    c[cle] += 1
                    formes.setdefault(cle, " ".join(f for _, f in fen))
        par_doc.append(c)
    total, docs = Counter(), Counter()
    for c in par_doc:
        total.update(c)
        docs.update(set(c))
    seuil_docs = mini_docs if len(textes) >= mini_docs else 1
    candidats = [k for k in total if docs[k] >= seuil_docs and total[k] >= 2]
    # Une expression incluse dans une plus longue aussi fréquente ne dit rien de plus.
    candidats.sort(key=lambda k: (-docs[k], -total[k], -len(k)))
    retenus: list[str] = []
    for k in candidats:
        if any(k in r and total[r] >= total[k] for r in retenus):
            continue
        retenus.append(k)
        if len(retenus) >= maxi:
            break
    return [{"expression": formes[k], "textes": docs[k], "occurrences": total[k]} for k in retenus]


# ─── HTML ─────────────────────────────────────────────────────────

IGNORES = {"head", "script", "style", "noscript", "svg", "template", "iframe", "canvas", "select",
           "button", "object", "video", "audio"}
HORS = {"nav", "footer", "form", "dialog"}          # jamais du contenu
ANNEXES = {"aside"}                                 # souvent du décor, parfois l'enveloppe de l'article
VIDES = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source",
         "track", "wbr"}
BLOCS = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th", "blockquote", "pre", "dd", "dt",
         "figcaption", "div", "section", "article", "main", "header", "tr", "summary", "details", "ul",
         "ol", "table", "dl", "figure", "caption", "address"}
# Éléments en ligne dont le texte ne se colle jamais au voisin (liens, boutons, libellés).
SEPARES = {"a", "button", "label", "option", "svg"}
# Une classe entière (« sub-menu », « site-navigation », « cookie-banner »), pas un fragment :
# « elementor-widget » ou « sidebar-layout » enveloppent souvent le contenu lui-même.
_DECOR = re.compile(r"(?:[a-z0-9]+[-_]){0,2}(?:nav|navbar|navigation|menu|sidebar|breadcrumbs?|fil-ariane|"
                    r"cookies?|cookie-(?:banner|notice|bar)|consent|comments?|commentaires|related(?:-posts)?|"
                    r"share|sharing|social-share|newsletter|popup|modal|pagination)", re.I)
_FAQ = re.compile(r"\bfaq\b|questions? (?:frequentes|courantes|posees)|foire aux questions")
_CTA = re.compile(r"\b(?:contactez|contacter|demandez|demander|reservez|reserver|telechargez|telecharger|"
                  r"essayez|essayer|appelez|decouvrez|inscrivez|prenez rendez-vous|prendre rendez-vous|"
                  r"devis|nous ecrire|ecrivez-nous|parlons|commencez|testez)\b")


class _Lecteur(HTMLParser):
    def __init__(self, url: str = "") -> None:
        super().__init__(convert_charrefs=True)
        self.url = url
        self.pile: list[tuple[str, set]] = []
        self.blocs: list[dict] = []
        self.tampon: list[str] = []
        self.type_bloc: tuple = ("texte",)
        self.elements: list[dict] = []
        self.titre, self.dans_titre = "", False
        self.metas: dict[str, str] = {}
        self.jsonld: list[str] = []
        self.dans_jsonld = False
        self.microdata: list[str] = []
        self.temps: list[str] = []

    # état de la pile
    def _a(self, drapeau: str) -> bool:
        return any(drapeau in d for _, d in self.pile)

    def _zone(self) -> dict:
        return {"hors": self._a("hors"), "annexe": self._a("annexe"), "entete": self._a("entete"),
                "main": self._a("main")}

    def _vider(self) -> None:
        texte = re.sub(r"\s+", " ", "".join(self.tampon)).strip()
        self.tampon = []
        if texte and not self._a("ignore"):
            genre = self.type_bloc
            self.blocs.append({"genre": genre[0], "niveau": genre[1] if len(genre) > 1 else None,
                               "texte": texte, **self._zone()})

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        if tag == "meta":
            cle = (a.get("name") or a.get("property") or a.get("itemprop") or "").lower()
            if cle and "content" in a:
                self.metas.setdefault(cle, a["content"])
            return
        if tag == "img":
            self.elements.append({"type": "img", "alt": a.get("alt", "").strip(), **self._zone()})
            return
        if tag == "br":
            self.tampon.append(" ")
            return
        if tag in VIDES:
            return
        if tag == "script" and "ld+json" in a.get("type", "").lower():
            self.dans_jsonld = True
            self.jsonld.append("")
        if tag == "title" and not self.titre:
            self.dans_titre = True
        if "itemtype" in a:
            self.microdata += [t.rstrip("/").rsplit("/", 1)[-1] for t in a["itemtype"].split()]
        if tag == "time" and a.get("datetime"):
            self.temps.append(a["datetime"])
        drapeaux = set()
        if tag in IGNORES:
            drapeaux.add("ignore")
        classes = f"{a.get('class', '')} {a.get('id', '')}".split()
        if tag == "header" and not self._a("main"):
            drapeaux.add("entete")
        if tag in HORS or a.get("role") in ("navigation", "contentinfo"):
            drapeaux.add("hors")
        elif tag in ANNEXES or a.get("role") == "complementary" or (
                tag not in ("html", "body", "main", "article") and any(_DECOR.fullmatch(c) for c in classes)):
            drapeaux.add("annexe")
        if tag in ("main", "article") or a.get("role") == "main":
            drapeaux.add("main")
        if tag in BLOCS or drapeaux:
            self._vider()          # le texte déjà lu appartient à la zone d'avant
        elif tag in SEPARES:
            self.tampon.append(" ")    # deux boutons côte à côte ne font pas un mot
        self.pile.append((tag, drapeaux))
        if tag in BLOCS:
            self.type_bloc = self._type_contextuel("p" if tag == "p" else "texte")
        if tag in ("ul", "ol", "table"):
            self.elements.append({"type": tag, **self._zone()})
        elif tag == "li":
            self.elements.append({"type": "li", **self._zone()})
        elif tag == "summary":
            self.elements.append({"type": "summary", **self._zone()})
        elif tag in ("strong", "b"):
            self.elements.append({"type": "gras", **self._zone()})
        elif tag == "a":
            href = a.get("href", "").strip()
            if href and not href.startswith(("#", "javascript:", "mailto:", "tel:")):
                self.elements.append({"type": "lien", "href": urljoin(self.url, href) if self.url else href,
                                      **self._zone()})

    def handle_endtag(self, tag):
        if tag in VIDES:
            return
        if tag == "title":
            self.dans_titre = False
        if tag == "script":
            self.dans_jsonld = False
        idx = next((i for i in range(len(self.pile) - 1, -1, -1) if self.pile[i][0] == tag), None)
        if idx is None:
            return
        if tag in BLOCS or any(d for _, d in self.pile[idx:]):
            self._vider()
        elif tag in SEPARES:
            self.tampon.append(" ")
        del self.pile[idx:]
        if tag in BLOCS:
            self.type_bloc = self._type_contextuel("texte")

    def _type_contextuel(self, defaut: str) -> tuple:
        """Le genre du bloc ouvert : le plus proche titre, puce ou cellule englobant l'emporte.

        Un <p> dans un <li> reste une puce ; un <span> dans un <h2> reste un titre.
        """
        for i in range(len(self.pile) - 1, -1, -1):
            t = self.pile[i][0]
            if re.fullmatch(r"h[1-6]", t):
                return ("titre", int(t[1]))
            if t == "li":
                parent = next((x for x, _ in reversed(self.pile[:i]) if x in ("ul", "ol")), "ul")
                return ("puce" if parent == "ul" else "numero",)
            if t in ("td", "th"):
                return ("cellule",)
            if t in ("ul", "ol", "table", "section", "article", "main", "body", "div", "blockquote") \
                    and i != len(self.pile) - 1:
                break
        return (defaut,)

    def handle_data(self, data):
        if self.dans_titre:
            self.titre += data
        if self.dans_jsonld:
            self.jsonld[-1] += data
            return
        if not self._a("ignore"):
            self.tampon.append(data)

    def close(self):
        super().close()
        self._vider()


def _types_schema(objet) -> list[str]:
    types = []
    if isinstance(objet, dict):
        t = objet.get("@type")
        types += [t] if isinstance(t, str) else [x for x in t if isinstance(x, str)] if isinstance(t, list) else []
        for v in objet.values():
            types += _types_schema(v)
    elif isinstance(objet, list):
        for v in objet:
            types += _types_schema(v)
    return types


def _dates_schema(objet, cles=("datePublished", "dateModified")) -> dict:
    trouve: dict[str, str] = {}
    if isinstance(objet, dict):
        for c in cles:
            if isinstance(objet.get(c), str):
                trouve.setdefault(c, objet[c])
        for v in objet.values():
            for c, d in _dates_schema(v, cles).items():
                trouve.setdefault(c, d)
    elif isinstance(objet, list):
        for v in objet:
            for c, d in _dates_schema(v, cles).items():
                trouve.setdefault(c, d)
    return trouve


def _jour(valeur: str | None) -> str | None:
    m = re.search(r"((?:19|20)\d\d-\d\d-\d\d)", valeur or "")
    return m.group(1) if m else None


def _hote(url: str) -> str:
    h = (urlparse(url).hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def en_markdown(blocs: list[dict]) -> str:
    lignes, n = [], 0
    for b in blocs:
        g = b["genre"]
        if g == "titre":
            lignes += ["", f"{'#' * b['niveau']} {b['texte']}", ""]
            n = 0
        elif g == "puce":
            lignes.append(f"- {b['texte']}")
        elif g == "numero":
            n += 1
            lignes.append(f"{n}. {b['texte']}")
        else:
            lignes += [b["texte"], ""]
            n = 0
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lignes)).strip()


def _page(url, titre, meta, blocs_tous, zone, elements_zone, schemas, dates, microdata_faq=False) -> dict:
    blocs = [b for b in blocs_tous if zone(b)]
    titres = [b for b in blocs if b["genre"] == "titre"]
    h1 = [b["texte"] for b in blocs_tous if b["genre"] == "titre" and b["niveau"] == 1 and not b["hors"]]
    plan: list[list] = []
    for b in titres:     # un sommaire ou une version mobile répètent les titres : un seul exemplaire
        if b["niveau"] in (2, 3) and [b["niveau"], b["texte"]] not in plan:
            plan.append([b["niveau"], b["texte"]])
    if h1:
        plan = [[1, h1[0]]] + plan
    texte = "\n".join(b["texte"] for b in blocs)
    compte = Counter(e["type"] for e in elements_zone)
    hote = _hote(url) if url else ""
    internes = externes = 0
    for e in elements_zone:
        if e["type"] != "lien":
            continue
        h = _hote(e["href"]) if e["href"].startswith(("http://", "https://")) else ""
        if not h or (hote and h == hote):
            internes += 1
        else:
            externes += 1
    imgs = [e for e in elements_zone if e["type"] == "img"]
    faq = (any(_FAQ.search(sans_accents(t["texte"])) for t in titres) or "FAQPage" in schemas
           or compte["summary"] >= 2 or microdata_faq)
    paragraphes = [b["texte"] for b in blocs if b["genre"] in ("p", "texte") and compter_mots(b["texte"]) >= 5]
    return {
        "url": url, "titre": re.sub(r"\s+", " ", titre).strip(), "meta": (meta or "").strip(),
        "h1": h1, "plan": plan, "mots": compter_mots(texte),
        "listes": {"puces": compte["ul"], "numerotees": compte["ol"], "items": compte["li"]},
        "tableaux": compte["table"], "images": len(imgs), "images_sans_alt": sum(1 for i in imgs if not i["alt"]),
        "liens_internes": internes, "liens_externes": externes, "gras": compte["gras"],
        "faq": bool(faq), "schemas": sorted(set(schemas)), "dates": dates,
        "questions_titres": [t["texte"] for t in titres if t["texte"].rstrip().endswith("?")],
        "texte": texte, "paragraphes": paragraphes, "markdown": en_markdown(blocs),
    }


def lire_html(html: str, url: str = "") -> dict:
    """Le contenu principal d'une page HTML et ses signaux, en un dictionnaire.

    Zone retenue : la plus étroite qui porte au moins 30 % du texte — <main> ou
    <article>, sinon le <body> sans barres latérales ni blocs reconnus à leur
    classe (menu, cookies, partage, commentaires…), sinon le <body> entier.
    Navigation, pied de page et formulaires ne comptent jamais.
    """
    lecteur = _Lecteur(url)
    try:
        lecteur.feed(html or "")
        lecteur.close()
    except Exception:  # noqa: BLE001 — une page mal formée se lit en partie, elle ne plante pas
        pass
    blocs, elements = lecteur.blocs, lecteur.elements
    zones = [lambda x: x["main"] and not (x["hors"] or x["annexe"]),       # <main>/<article>, sans décor
             lambda x: not (x["hors"] or x["annexe"] or x["entete"]),     # le corps, sans décor
             lambda x: not (x["hors"] or x["entete"])]                    # le corps, décor supposé compris
    mots = [sum(compter_mots(b["texte"]) for b in blocs if z(b)) for z in zones]
    # La zone la plus étroite qui porte au moins 30 % du texte de la page : un <main> de
    # 150 mots sur une page de 2 500 n'est pas l'article, c'est un fragment.
    zone = next((z for z, n in zip(zones, mots) if n >= 30 and n >= 0.3 * mots[2]), zones[2])
    schemas, dates_ld = [], {}
    for brut in lecteur.jsonld:
        try:
            objet = json.loads(brut.strip())
        except ValueError:
            schemas += re.findall(r'"@type"\s*:\s*"([^"]+)"', brut)
            continue
        schemas += _types_schema(objet)
        for c, d in _dates_schema(objet).items():
            dates_ld.setdefault(c, d)
    schemas += lecteur.microdata
    m = lecteur.metas
    dates = {
        "publiee": _jour(dates_ld.get("datePublished") or m.get("article:published_time") or m.get("datepublished")),
        "modifiee": _jour(dates_ld.get("dateModified") or m.get("article:modified_time") or m.get("og:updated_time")
                          or m.get("datemodified") or (max(lecteur.temps) if lecteur.temps else None)),
    }
    meta = m.get("description") or m.get("og:description") or ""
    return _page(url, lecteur.titre, meta, blocs, zone, [e for e in elements if zone(e)], schemas, dates)


def lire_markdown(md: str, url: str = "") -> dict:
    """Même lecture qu'`lire_html`, pour un texte Markdown (fichier, ou rendu d'un service)."""
    blocs, elements, para = [], [], []
    titre = ""
    en_tableau = False

    def propre(t: str) -> str:
        t = re.sub(r"!\[([^\]]*)\]\([^)]*\)", "", t)
        t = re.sub(r"\[([^\]]*)\]\(([^)]*)\)", r"\1", t)
        return re.sub(r"[*_`]{1,3}", "", t).strip()

    def fermer():
        if para:
            blocs.append({"genre": "p", "niveau": None, "texte": propre(" ".join(para)), **zone})
            para.clear()

    zone = {"hors": False, "annexe": False, "entete": False, "main": True}
    for ligne in (md or "").splitlines():
        s = ligne.strip()
        for alt in re.findall(r"!\[([^\]]*)\]\([^)]*\)", s):
            elements.append({"type": "img", "alt": alt.strip(), **zone})
        for cible in re.findall(r"(?<!!)\[[^\]]*\]\(([^)\s]+)", s):
            elements.append({"type": "lien", "href": urljoin(url, cible) if url else cible, **zone})
        elements += [{"type": "gras", **zone}] * len(re.findall(r"\*\*[^*]+\*\*", s))
        h = re.match(r"(#{1,6})\s+(.*?)\s*#*$", s)
        li = re.match(r"([-*+]|\d+[.)])\s+(.*)", s)
        if not s:
            fermer()
            en_tableau = False
        elif h:
            fermer()
            blocs.append({"genre": "titre", "niveau": len(h.group(1)), "texte": propre(h.group(2)), **zone})
            titre = titre or (propre(h.group(2)) if len(h.group(1)) == 1 else "")
        elif li:
            fermer()
            num = li.group(1)[0].isdigit()
            prec = blocs[-1]["genre"] if blocs else ""
            if prec != ("numero" if num else "puce"):
                elements.append({"type": "ol" if num else "ul", **zone})
            elements.append({"type": "li", **zone})
            blocs.append({"genre": "numero" if num else "puce", "niveau": None, "texte": propre(li.group(2)), **zone})
        elif s.startswith("|"):
            fermer()
            if not en_tableau:
                elements.append({"type": "table", **zone})
                en_tableau = True
            if not re.fullmatch(r"[|\s:-]+", s):
                blocs.append({"genre": "cellule", "niveau": None,
                              "texte": " · ".join(propre(c) for c in s.strip("|").split("|") if c.strip()), **zone})
        elif s.startswith(">"):
            fermer()
            blocs.append({"genre": "texte", "niveau": None, "texte": propre(s.lstrip("> ")), **zone})
        else:
            para.append(s)
    fermer()
    return _page(url, titre, "", blocs, lambda b: True, elements, [], {"publiee": None, "modifiee": None})


def lire_texte_brut(texte: str, url: str = "") -> dict:
    """Un .txt : un paragraphe par bloc séparé d'une ligne vide."""
    return lire_markdown("\n\n".join(re.sub(r"\s+", " ", b) for b in re.split(r"\n\s*\n", texte or "")), url)


def ouverture(page: dict) -> str:
    """Le type d'attaque du premier paragraphe : question, chiffre, adresse, définition, autre."""
    signature = re.compile(r"min(?:utes)? de lecture|publie le|mis a jour le|ecrit par")
    premier = next((p for p in page.get("paragraphes") or [] if not signature.search(sans_accents(p))), "")
    phrase = next(iter(decouper_phrases(premier)), "")
    s = sans_accents(phrase)
    if not s:
        return "n.d."
    if phrase.rstrip().endswith("?"):
        return "question"
    if re.search(r"\d", " ".join(s.split()[:8])):
        return "chiffre"
    if re.match(r"(?:vous|votre|vos|tu|ton|ta|tes)\b", s):
        return "adresse directe"
    if re.search(r"\b(?:est|sont|designe|designent|consiste|correspond) (?:un|une|le|la|les|l'|a|en)\b", s):
        return "définition"
    return "situation / affirmation"


def cloture_avec_appel(page: dict) -> bool:
    """Le dernier paragraphe pousse-t-il à une action (contacter, demander, essayer…) ?"""
    paras = page.get("paragraphes") or []
    derniers = paras[-2:] if paras and compter_mots(paras[-1]) < 12 else paras[-1:]
    return bool(derniers) and any(_CTA.search(sans_accents(p)) for p in derniers)


# ─── Statistiques ─────────────────────────────────────────────────

def centile(valeurs: list[float], p: float) -> float | None:
    """Centile par interpolation linéaire (même convention que les tableurs)."""
    v = sorted(valeurs)
    if not v:
        return None
    k = (len(v) - 1) * p / 100
    bas, haut = math.floor(k), math.ceil(k)
    return float(v[bas]) if bas == haut else v[bas] + (v[haut] - v[bas]) * (k - bas)


def mediane(valeurs: list[float]) -> float | None:
    return centile(valeurs, 50)


# ─── Réseau ───────────────────────────────────────────────────────

class PageIllisible(RuntimeError):
    pass


def verifier_url(url: str) -> None:
    """Refuse ce qui n'est pas http(s) public : une URL de SERP ne doit pas viser le réseau local."""
    d = urlparse(url)
    if d.scheme not in ("http", "https") or not d.hostname:
        raise PageIllisible("URL non http(s)")
    try:
        infos = socket.getaddrinfo(d.hostname, None)
    except socket.gaierror as exc:
        raise PageIllisible(f"domaine introuvable ({exc.strerror})") from None
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise PageIllisible("adresse interne refusée")


def telecharger(url: str, delai: float = 15.0, langue: str = "fr") -> tuple[str, str]:
    """(HTML, URL finale). Lève PageIllisible si la page ne se lit pas : jamais d'exception brute."""
    verifier_url(url)
    requete = urllib.request.Request(url, headers={"User-Agent": AGENT, "Accept": "text/html,application/xhtml+xml",
                                                   "Accept-Language": f"{langue},en;q=0.5"})
    try:
        with urllib.request.urlopen(requete, timeout=delai) as rep:
            genre = rep.headers.get("Content-Type", "")
            if genre and "html" not in genre.lower():
                raise PageIllisible(f"pas une page HTML ({genre.split(';')[0]})")
            brut = rep.read(TAILLE_MAX + 1)
            jeu = rep.headers.get_content_charset()
            finale = rep.geturl()
    except urllib.error.HTTPError as exc:
        raise PageIllisible(f"HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise PageIllisible(str(getattr(exc, "reason", exc))[:80]) from None
    if len(brut) > TAILLE_MAX:
        raise PageIllisible("page de plus de 5 Mo")
    if not jeu:
        m = re.search(rb"<meta[^>]+charset=[\"']?([\w-]+)", brut[:4096], re.I)
        jeu = m.group(1).decode() if m else "utf-8"
    try:
        return brut.decode(jeu, errors="replace"), finale
    except LookupError:
        return brut.decode("utf-8", errors="replace"), finale
