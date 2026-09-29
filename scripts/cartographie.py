#!/usr/bin/env python3
"""Cartographie d'un site : une page, un mot-clé principal, un prompt principal.

    python3 cartographie.py initialiser                     # Search Console 90 jours + sitemap + calendrier
    python3 cartographie.py initialiser --csv export.csv --sans-sitemap
    python3 cartographie.py mensuel --mois 2026-09          # → rapports/cartographie-2026-09.md
    python3 cartographie.py mensuel --mois 2026-09 --volumes --prompts    # payant : DataForSEO, moteurs IA
    python3 cartographie.py verifier                        # cannibalisation, prompts hors règles
    python3 cartographie.py exporter --notion-csv           # CSV prêt pour un import Notion

Le tableau vit dans le projet, `memoire/cartographie.csv`, une ligne par page
(ou par page à créer). Colonnes :

    url, statut (existante | a-creer | en-cours | publiee),
    type (pilier | cluster | offre | outil | lead-magnet | article), silo, cluster,
    mot_cle_principal, mots_cles_secondaires, prompt_principal, langue,
    intention, funnel, priorite (P1 | P2 | P3), volume, kd,
    a_valider, derniere_maj, notes

Règles :
- un mot-clé principal par page, et une page par mot-clé principal : deux
  lignes qui partagent le même mot-clé, c'est une cannibalisation annoncée ;
- un prompt principal par page : la question qu'un acheteur pose à ChatGPT,
  Gemini ou Claude, et que la page doit gagner ;
- `initialiser` complète, il n'écrase jamais : une cellule remplie reste telle
  quelle. Seule exception : une ligne « a-creer » dont la page existe désormais
  (journal ou Search Console) reçoit son URL et passe à « publiee » ;
- ce que le script propose (mot-clé tiré de Search Console, prompt tiré d'un
  gabarit) est listé dans la colonne `a_valider`. Videz-la une fois la ligne
  validée avec le client.

`mensuel` écrit une ligne par page et par mois dans
`donnees/cartographie-historique.csv`, et le tableau du mois dans
`rapports/cartographie-AAAA-MM.md` (+ `.json`). Position et clics y sont ceux
de la page SUR son mot-clé principal (croisement page × requête), pas ceux de
la page toutes requêtes confondues. La visibilité IA reprend les derniers
relevés de share_of_model.py ; `--prompts` interroge les moteurs sur les
prompts de la cartographie (payant, désactivé par défaut).

Sans dépendance.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import charger_env, lire_liste, lire_valeur, racine_projet  # noqa: E402
import opportunites  # noqa: E402
import rapport  # noqa: E402
import share_of_model  # noqa: E402

FICHIER = "memoire/cartographie.csv"
HISTORIQUE = "donnees/cartographie-historique.csv"

COLONNES = ["url", "statut", "type", "silo", "cluster", "mot_cle_principal", "mots_cles_secondaires",
            "prompt_principal", "langue", "intention", "funnel", "priorite", "volume", "kd",
            "a_valider", "derniere_maj", "notes"]
STATUTS = ("existante", "a-creer", "en-cours", "publiee")
TYPES = ("pilier", "cluster", "offre", "outil", "lead-magnet", "article")

MOTEURS = ("openai", "gemini", "claude", "perplexity")
NOMS_MOTEURS = {"openai": "ChatGPT", "gemini": "Gemini", "claude": "Claude", "perplexity": "Perplexity"}
ALIAS_MOTEURS = {"openai": "openai", "chatgpt": "openai", "gpt": "openai", "gemini": "gemini",
                 "claude": "claude", "anthropic": "claude", "perplexity": "perplexity"}

COLONNES_HISTORIQUE = [
    "mois", "cle", "url", "mot_cle_principal", "prompt_principal", "statut",
    "clics", "impressions", "ctr", "position", "clics_prec", "impressions_prec", "position_prec",
    "clics_mc", "impressions_mc", "ctr_mc", "position_mc", "clics_mc_prec", "position_mc_prec",
    "delta_position_mc", "delta_clics_mc", "page_mieux_placee",
    "ia_openai", "ia_gemini", "ia_claude", "ia_perplexity", "ia_mesure", "ia_concurrent", "ia_evolution",
    "action_notion", "action"]

INTENTIONS = {"informational": "informationnel", "commercial": "commercial", "transactional": "transactionnel",
              "navigational": "navigationnel", "informationnel": "informationnel",
              "transactionnel": "transactionnel", "navigationnel": "navigationnel"}
INTENTION_DU_FUNNEL = {"TOFU": "informationnel", "MOFU": "commercial", "BOFU": "transactionnel"}
FUNNEL_DE_INTENTION = {"informationnel": "TOFU", "commercial": "MOFU", "transactionnel": "BOFU", "navigationnel": "BOFU"}

# Gabarits de prompt par langue et par intention. {k} = mot-clé principal.
# Ce sont des propositions : l'agent les reformule au ton parlé avec le client.
GABARITS = {
    "fr": {"informationnel": "Que faut-il savoir sur {k} ?",
           "commercial": "Quelles options comparer pour {k}, et sur quels critères ?",
           "transactionnel": "Qui me recommandes-tu pour {k} ?",
           "navigationnel": "Où trouver {k} ?"},
    "en": {"informationnel": "What should I know about {k}?",
           "commercial": "Which options should I compare for {k}, and on what criteria?",
           "transactionnel": "Who would you recommend for {k}?",
           "navigationnel": "Where can I find {k}?"},
    "ar": {"informationnel": "ما الذي يجب أن أعرفه عن {k}؟",
           "commercial": "ما الخيارات التي يجب مقارنتها بخصوص {k}، وبأي معايير؟",
           "transactionnel": "من تنصحني به بخصوص {k}؟",
           "navigationnel": "أين أجد {k}؟"},
}
# Un mot-clé déjà formulé en question est le meilleur prompt possible : on le garde.
QUESTION = re.compile(r"^(comment|pourquoi|quel(le)?s?|combien|qu['’ ]est|est[- ]ce|quand|où|faut[- ]il|peut[- ]on"
                      r"|dois[- ]je|how|what|why|which|when|where|who|can|is|are|do|does|should"
                      r"|هل|كيف|ماذا|لماذا|متى|أين|كم)(?=[\s\-']|$)", re.I)
ARABE = re.compile(r"[؀-ۿ]")
ANGLAIS = re.compile(r"\b(the|how|what|why|which|best|for|with|near|company|cost|price|guide to|near me)\b", re.I)
FRANCAIS = re.compile(r"\b(le|la|les|des|du|de|pour|avec|comment|quel|quelle|prix|pas cher)\b", re.I)


# ─── Normalisation ────────────────────────────────────────────────

def normaliser_url(url: str) -> str:
    """Clé de rapprochement : sans protocole, sans www, sans paramètres ni barre finale."""
    u = (url or "").strip().split("#")[0].split("?")[0]
    return re.sub(r"^https?://(www\.)?", "", u, flags=re.I).rstrip("/").lower()


def normaliser_requete(q: str) -> str:
    return " ".join((q or "").lower().split())


def cle_de(ligne: dict) -> str:
    """Une page existante se reconnaît à son URL ; une page à créer, à son mot-clé."""
    url = (ligne.get("url") or "").strip()
    return normaliser_url(url) if url else "mc:" + normaliser_requete(ligne.get("mot_cle_principal", ""))


def chemin_de(url: str) -> str:
    """Chemin de l'URL, avec ou sans protocole (les clés normalisées n'en ont pas)."""
    return re.sub(r"^(https?://)?[^/]+", "", url or "") or "/"


def _num(v) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        return None


def _fr(v: float | None, decimales: int = 1, signe: bool = False) -> str:
    if v is None:
        return "—"
    texte = f"{v:+.{decimales}f}" if signe else f"{v:.{decimales}f}"
    return texte.replace(".", ",")


def drapeaux(ligne: dict) -> list[str]:
    return [d for d in re.split(r"[;,\s]+", ligne.get("a_valider") or "") if d]


# ─── Lecture et écriture du tableau ───────────────────────────────

def lire_cartographie(chemin: Path) -> tuple[list[dict], list[str]]:
    """Lignes et en-tête. Les colonnes ajoutées à la main sont conservées."""
    if not chemin.is_file():
        return [], list(COLONNES)
    with chemin.open(encoding="utf-8-sig", newline="") as f:
        lecteur = csv.DictReader(f)
        entete = list(lecteur.fieldnames or [])
        lignes = [{k: (v or "") for k, v in l.items() if k} for l in lecteur]
    entete += [c for c in COLONNES if c not in entete]
    for l in lignes:
        for c in entete:
            l.setdefault(c, "")
    return [l for l in lignes if any(str(v).strip() for v in l.values())], entete


def ecrire_csv(chemin: Path, lignes: list[dict], entete: list[str]) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=entete, extrasaction="ignore")
        w.writeheader()
        w.writerows(lignes)


def langue_projet() -> str:
    langues = lire_liste("projet.langues")
    return (lire_valeur("sorties.langue") or lire_valeur("projet.langue_cible")
            or (langues[0] if langues else "") or "fr").lower()[:2]


# ─── Initialiser : calculs purs ───────────────────────────────────

def choisir_mot_cle(lignes: list[dict], marque: list[re.Pattern]) -> tuple[str, list[str]]:
    """Mot-clé principal d'une page : la requête hors marque qui apporte le plus
    de clics, à défaut d'impressions. Renvoie (principal, 3 secondaires)."""
    agreg: dict[str, list] = {}
    for l in lignes:
        q = normaliser_requete(l.get("requete", ""))
        if not q or any(m.search(q) for m in marque):
            continue
        a = agreg.setdefault(q, [0.0, 0.0, q])
        a[0] += float(l.get("clics") or 0)
        a[1] += float(l.get("impressions") or 0)
    tri = sorted(agreg.values(), key=lambda a: (-a[0], -a[1], a[2]))
    if not tri:
        return "", []
    return tri[0][2], [a[2] for a in tri[1:4] if a[1] > 0]


def propositions_gsc(lignes: list[dict], marque: list[re.Pattern], impressions_min: int = 10) -> list[dict]:
    """Une proposition par page vue dans Search Console (lignes requête × page)."""
    par_page: dict[str, dict] = {}
    for l in lignes:
        if not l.get("page"):
            continue
        d = par_page.setdefault(normaliser_url(l["page"]), {"url": l["page"], "lignes": [], "clics": 0.0, "impr": 0.0})
        d["lignes"].append(l)
        d["clics"] += float(l.get("clics") or 0)
        d["impr"] += float(l.get("impressions") or 0)
    props = []
    for d in sorted(par_page.values(), key=lambda d: (-d["clics"], -d["impr"])):
        if d["impr"] < impressions_min:
            continue
        principal, secondaires = choisir_mot_cle(d["lignes"], marque)
        props.append({"url": d["url"], "statut": "existante", "mot_cle_principal": principal,
                      "mots_cles_secondaires": " | ".join(secondaires), "_source": "gsc"})
    return props


def urls_du_sitemap(xml: str) -> tuple[list[str], bool]:
    """(adresses <loc>, vrai si c'est un index de sitemaps). Les <image:loc> sont ignorées."""
    locs = [html.unescape(u) for u in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml)]
    return locs, "<sitemapindex" in xml


PAS_UNE_PAGE = re.compile(r"\.(pdf|jpe?g|png|gif|webp|svg|xml|zip|mp4)$|/(tag|tags|category|categorie|author|auteur"
                          r"|feed|page/\d+)(/|$)", re.I)


def lire_calendrier(texte: str) -> list[dict]:
    """Lignes du tableau de rapports/calendrier-*.md (opportunites.py --calendrier)."""
    lignes = []
    for brute in texte.splitlines():
        if not brute.strip().startswith("|"):
            continue
        c = [x.strip() for x in brute.strip().strip("|").split("|")]
        if len(c) < 8 or c[0].lower() == "semaine" or not c[0] or set(c[0]) <= set("-: "):
            continue
        lignes.append({"semaine": c[0], "type": c[1], "funnel": c[2], "requete": c[3], "page": c[4],
                       "action": c[5], "schema": c[6], "statut": c[7]})
    return lignes


def propositions_calendrier(calendrier: list[dict]) -> list[dict]:
    """Les créations planifiées sans page existante deviennent des lignes « a-creer »."""
    return [{"url": "", "statut": "a-creer", "mot_cle_principal": normaliser_requete(e["requete"]),
             "funnel": e["funnel"] if e["funnel"] in ("TOFU", "MOFU", "BOFU") else "", "_source": "calendrier"}
            for e in calendrier
            if e["type"].startswith("cr") and e["page"].lower() in ("à créer", "a créer", "a-creer", "") and e["requete"]]


def langue_de(mot_cle: str, url: str = "", defaut: str = "fr") -> str:
    if ARABE.search(mot_cle or ""):
        return "ar"
    m = re.match(r"^/(fr|en|ar)(/|$)", chemin_de(url).lower())
    if m:
        return m.group(1)
    if ANGLAIS.search(mot_cle or "") and not FRANCAIS.search(mot_cle or ""):
        return "en"
    return defaut


def type_de(url: str) -> str:
    """Première proposition de type, d'après l'URL. Pilier et cluster se décident à la main."""
    chemin = chemin_de(url).lower().rstrip("/")
    if not chemin:
        return "offre"
    if re.search(r"simulat|calculat|calculette|outil|tool|generat|comparateur|estimat", chemin):
        return "outil"
    if re.search(r"mod[eè]le|template|checklist|ebook|livre-blanc|telecharg|download", chemin):
        return "lead-magnet"
    if re.search(r"/(blog|actualites?|articles?|news|guides?|ressources|magazine|conseils)(/|$)", chemin):
        return "article"
    if re.search(r"services?|offres?|tarifs?|prix|pricing|devis|contact|prestations?|solutions?|accompagnement", chemin):
        return "offre"
    return ""


def proposer_prompt(mot_cle: str, intention: str, langue: str = "fr", categorie: str = "") -> str:
    """La question qu'un acheteur poserait à un assistant IA, et que la page doit gagner."""
    k = " ".join((mot_cle or "").split())
    if not k:
        return ""
    fin = {"fr": " ?", "en": "?", "ar": "؟"}.get(langue, " ?")
    if QUESTION.match(k):
        k = k[0].upper() + k[1:]
        return k if k.rstrip().endswith(("?", "؟")) else k.rstrip() + fin
    funnel = FUNNEL_DE_INTENTION.get(intention, "TOFU")
    if categorie and langue in share_of_model.GABARITS and funnel in ("MOFU", "BOFU"):
        # Même gabarit que la batterie share_of_model : les deux mesures restent comparables.
        return share_of_model.GABARITS[langue][funnel][0].format(c=categorie, s=k, p="")
    gabarits = GABARITS.get(langue, GABARITS["fr"])
    return gabarits.get(intention, gabarits["informationnel"]).format(k=k)


def completer(p: dict, lexique: list, demande: dict, langue_defaut: str = "fr", categorie: str = "") -> dict:
    """Ajoute langue, funnel, intention, prompt, type, silo, priorité, volume et KD à une proposition."""
    mc, url = p.get("mot_cle_principal", ""), p.get("url", "")
    p.setdefault("type", type_de(url) if url else "")
    if not mc:
        p["a_valider"] = "mot_cle_principal"
        return p
    langue = langue_de(mc, url, langue_defaut)
    d = demande.get(normaliser_requete(mc), {})
    funnel = p.get("funnel") or opportunites.funnel_de(url, mc)
    intention = INTENTIONS.get((d.get("intention") or "").lower()) or INTENTION_DU_FUNNEL.get(funnel, "informationnel")
    p.update(langue=langue, funnel=funnel, intention=intention,
             # La catégorie est écrite dans la langue du projet : inutile dans un prompt d'une autre langue.
             prompt_principal=proposer_prompt(mc, intention, langue, categorie if langue == langue_defaut else ""),
             volume=d.get("volume", ""), kd=d.get("kd", ""))
    if lexique:
        theme, valeur = opportunites.theme_de(mc, lexique)
        if theme != "hors-lexique":
            p.update(silo=theme, priorite={3: "P1", 2: "P2"}.get(valeur, "P3"))
    p["a_valider"] = ";".join((["mot_cle_principal"] if p.get("_source") == "gsc" else []) + ["prompt_principal"])
    return p


def completer_saisies(lignes: list[dict], lexique: list, demande: dict, langue_defaut: str = "fr",
                      categorie: str = "") -> int:
    """Mot-clé principal saisi à la main (ou importé d'un plan) sans prompt : proposer le reste.

    Seules les cellules vides sont remplies ; le prompt proposé est marqué à valider."""
    n = 0
    for l in lignes:
        if not l.get("mot_cle_principal") or l.get("prompt_principal"):
            continue
        p = completer({"url": l.get("url", ""), "mot_cle_principal": l["mot_cle_principal"],
                       "funnel": l.get("funnel", "")}, lexique, demande, langue_defaut, categorie)
        for cle, val in p.items():
            if cle in ("a_valider", "url", "mot_cle_principal") or val in ("", None) or l.get(cle):
                continue
            l[cle] = str(val)
        drapeaux_ligne = [d for d in (l.get("a_valider") or "").split(";") if d]
        if "prompt_principal" not in drapeaux_ligne:
            l["a_valider"] = ";".join(drapeaux_ligne + ["prompt_principal"])
        n += 1
    return n


def fusionner(existantes: list[dict], propositions: list[dict], date: str,
              publiees: dict[str, str] | None = None) -> dict:
    """Complète le tableau sans jamais écraser une cellule remplie.

    `publiees` : requête → URL, d'après le journal (pages neuves publiées). Une
    ligne « a-creer » dont le mot-clé y figure reçoit son URL et passe à « publiee ».
    Modifie `existantes` en place ; renvoie le compte des ajouts et compléments.
    """
    stats = {"ajoutees": 0, "completees": 0, "publiees": 0}
    publiees = {normaliser_requete(k): v for k, v in (publiees or {}).items()}

    def a_creer_sur(mc: str) -> dict | None:
        return next((l for l in existantes if not l.get("url") and l.get("statut") in ("a-creer", "en-cours")
                     and normaliser_requete(l.get("mot_cle_principal", "")) == mc), None)

    for l in existantes:
        mc = normaliser_requete(l.get("mot_cle_principal", ""))
        if not l.get("url") and l.get("statut") in ("a-creer", "en-cours") and mc in publiees:
            l.update(url=publiees[mc], statut="publiee", derniere_maj=date)
            stats["publiees"] += 1

    index = {cle_de(l): l for l in existantes}
    principaux = {normaliser_requete(l.get("mot_cle_principal", "")) for l in existantes} - {""}
    for brute in propositions:
        p = {k: v for k, v in brute.items() if not k.startswith("_")}
        mc = normaliser_requete(p.get("mot_cle_principal", ""))
        cible = index.get(cle_de(p))
        if cible is None and p.get("url") and mc:
            cible = a_creer_sur(mc)                     # la page prévue existe désormais
            if cible is not None:
                cible.update(url=p["url"], statut="publiee", derniere_maj=date)
                index[cle_de(cible)] = cible
                stats["publiees"] += 1
        if cible is None:
            if not p.get("url") and mc in principaux:
                continue                                # déjà le mot-clé d'une page : pas de doublon
            nouvelle = {c: "" for c in COLONNES}
            nouvelle.update({k: ("" if v is None else str(v)) for k, v in p.items()})
            nouvelle["derniere_maj"] = date
            existantes.append(nouvelle)
            index[cle_de(nouvelle)] = nouvelle
            principaux.add(mc)
            stats["ajoutees"] += 1
            continue
        remplies = []
        for c, v in p.items():
            if c in ("a_valider", "derniere_maj") or v in ("", None):
                continue
            if not str(cible.get(c, "")).strip():
                cible[c] = str(v)
                remplies.append(c)
        if remplies:
            proposes = [d for d in drapeaux(p) if d in remplies]
            cible["a_valider"] = ";".join(dict.fromkeys(drapeaux(cible) + proposes))
            cible["derniere_maj"] = date
            stats["completees"] += 1
    return stats


def doublons(lignes: list[dict]) -> dict[str, list[str]]:
    """Mots-clés principaux portés par plusieurs lignes : la cannibalisation annoncée."""
    par_mc: dict[str, list[str]] = {}
    for l in lignes:
        mc = normaliser_requete(l.get("mot_cle_principal", ""))
        if mc:
            par_mc.setdefault(mc, []).append(chemin_de(l["url"]) if l.get("url") else "(à créer)")
    return {mc: pages for mc, pages in par_mc.items() if len(pages) > 1}


# ─── Initialiser : collecte ───────────────────────────────────────

def lire_demande_locale(racine: Path) -> dict[str, dict]:
    """Volumes, KD et intention déjà achetés (donnees/demande-*.csv) : réutilisés sans nouvel appel."""
    demande: dict[str, dict] = {}
    for f in sorted((racine / "donnees").glob("demande-*.csv")):
        with f.open(encoding="utf-8-sig", newline="") as fh:
            for l in csv.DictReader(fh):
                q = normaliser_requete(l.get("requete") or l.get("keyword") or "")
                if q:
                    demande[q] = {"volume": l.get("volume", ""), "kd": l.get("kd", ""),
                                  "intention": l.get("intention", "")}
    return demande


def lire_sitemap(url: str, maximum: int = 500) -> list[str]:
    def charger(u: str) -> str:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (compatible; decupler-seo cartographie)"})
        with urllib.request.urlopen(req, timeout=20) as rep:
            return rep.read(10_000_000).decode("utf-8", "replace")
    locs, index = urls_du_sitemap(charger(url))
    if index:
        pages = []
        for sous in locs[:20]:
            try:
                pages += urls_du_sitemap(charger(sous))[0]
            except Exception as exc:  # un sous-sitemap cassé n'arrête pas les autres
                print(f"  ! sitemap {sous} : {str(exc)[:80]}", file=sys.stderr)
            if len(pages) >= maximum:
                break
        locs = pages
    return [u for u in locs if not PAS_UNE_PAGE.search(u)][:maximum]


def cmd_initialiser(a) -> int:
    racine = racine_projet()
    chemin = racine / FICHIER
    lignes_carto, entete = lire_cartographie(chemin)
    marque = opportunites.motifs_marque()
    propositions: list[dict] = []

    if a.csv:
        gsc_lignes, source = opportunites.lire_csv_gsc(Path(a.csv)), f"export {Path(a.csv).name}"
    else:
        try:
            gsc_lignes, source = opportunites.lire_gsc(a.jours, a.site), f"Search Console, {a.jours} jours"
        except Exception as exc:  # ErreurGSC, réseau : on continue avec le sitemap et le calendrier
            print(f"  ! Search Console indisponible ({str(exc)[:100]}) : pas de mot-clé tiré des données",
                  file=sys.stderr)
            gsc_lignes, source = [], "sans Search Console"
    propositions += propositions_gsc(gsc_lignes, marque, a.impressions_min)

    if not a.sans_sitemap:
        domaine = lire_valeur("projet.domaine")
        url_sitemap = a.sitemap or (("" if "//" in domaine else "https://") + domaine.rstrip("/") + "/sitemap.xml"
                                    if domaine else "")
        if url_sitemap:
            try:
                urls = lire_sitemap(url_sitemap, a.sitemap_max)
                propositions += [{"url": u, "statut": "existante", "_source": "sitemap"} for u in urls]
                print(f"  ✓ sitemap : {len(urls)} page(s)")
            except Exception as exc:
                print(f"  ! sitemap injoignable ({url_sitemap}) : {str(exc)[:80]}", file=sys.stderr)

    calendriers = sorted((racine / "rapports").glob("calendrier-*.md"))
    if calendriers:
        prevues = propositions_calendrier(lire_calendrier(calendriers[-1].read_text(encoding="utf-8")))
        propositions += prevues
        print(f"  ✓ {calendriers[-1].name} : {len(prevues)} page(s) à créer")

    lexique = opportunites.lire_lexique(racine / "memoire" / "lexique.csv")
    demande = lire_demande_locale(racine)
    for p in propositions:
        completer(p, lexique, demande, langue_projet(), a.categorie)
    stats = fusionner(lignes_carto, propositions, dt.date.today().isoformat(), opportunites.pages_ciblees())
    stats["completees"] += completer_saisies(lignes_carto, lexique, demande, langue_projet(), a.categorie)

    print(f"\n  {source} · {stats['ajoutees']} ligne(s) ajoutée(s), {stats['completees']} complétée(s), "
          f"{stats['publiees']} page(s) prévue(s) désormais publiée(s)")
    if a.dry_run:
        print("  (--dry-run : rien d'écrit)\n")
    else:
        ecrire_csv(chemin, lignes_carto, entete)
        print(f"  ✓ {FICHIER} · {len(lignes_carto)} ligne(s)")
    signaler(lignes_carto)
    return 0


def signaler(lignes: list[dict]) -> int:
    """Affiche les points à traiter ; renvoie le nombre d'erreurs bloquantes (cannibalisation)."""
    cannib = doublons(lignes)
    for mc, pages in cannib.items():
        print(f"  ✗ cannibalisation : « {mc} » est le mot-clé principal de {len(pages)} pages ({', '.join(pages)})")
    sans_mc = [l for l in lignes if not l.get("mot_cle_principal")]
    sans_prompt = [l for l in lignes if l.get("mot_cle_principal") and not l.get("prompt_principal")]
    a_valider = [l for l in lignes if drapeaux(l)]
    # Mêmes règles que la batterie share_of_model : pas de marque, 20 mots au plus, pas de ton vendeur.
    marque, domaine = lire_valeur("projet.nom"), lire_valeur("projet.domaine")
    for l in lignes:
        if l.get("prompt_principal"):
            erreurs, _ = share_of_model.verifier([{"famille": "visibilite", "prompt": l["prompt_principal"]}],
                                                 marque, domaine)
            for e in erreurs:
                print(f"  ! prompt de {chemin_de(l['url']) if l.get('url') else l.get('mot_cle_principal')} : "
                      f"{e.split(' : ', 1)[-1]}")
    repetes = Counter(normaliser_requete(l["prompt_principal"]) for l in lignes if l.get("prompt_principal"))
    for prompt, n in repetes.items():
        if n > 1:
            print(f"  ! le prompt « {prompt} » est le prompt principal de {n} lignes : un prompt, une page")
    print(f"  {len(a_valider)} ligne(s) à valider avec le client · {len(sans_mc)} sans mot-clé principal · "
          f"{len(sans_prompt)} sans prompt principal\n")
    return len(cannib)


def cmd_verifier(a) -> int:
    lignes, _ = lire_cartographie(racine_projet() / FICHIER)
    if not lignes:
        print(f"  ✗ {FICHIER} vide ou absent : lancez d'abord « initialiser »")
        return 1
    for l in lignes:
        if l.get("statut") and l["statut"] not in STATUTS:
            print(f"  ! {l.get('url') or l.get('mot_cle_principal')} : statut « {l['statut']} » inconnu ({', '.join(STATUTS)})")
        if l.get("type") and l["type"] not in TYPES:
            print(f"  ! {l.get('url') or l.get('mot_cle_principal')} : type « {l['type']} » inconnu ({', '.join(TYPES)})")
    return 1 if signaler(lignes) else 0


# ─── Mensuel : calculs purs ───────────────────────────────────────

def indexer(lignes: list[dict], par_requete: bool = False) -> dict:
    """Agrège par page (ou page × requête) : clics, impressions, ctr (%), position pondérée."""
    idx: dict = {}
    for l in lignes:
        cle = normaliser_url(l["page"])
        if par_requete:
            cle = (cle, normaliser_requete(l["requete"]))
        a = idx.setdefault(cle, {"clics": 0.0, "impressions": 0.0, "pos_x": 0.0})
        a["clics"] += float(l.get("clics") or 0)
        a["impressions"] += float(l.get("impressions") or 0)
        a["pos_x"] += float(l.get("position") or 0) * float(l.get("impressions") or 0)
    for a in idx.values():
        impr = a["impressions"]
        a["position"] = round(a.pop("pos_x") / impr, 1) if impr else None
        a["ctr"] = round(a["clics"] / impr * 100, 2) if impr else 0.0
        a["clics"], a["impressions"] = round(a["clics"]), round(a["impressions"])
    return idx


def etat_ia(ligne: dict) -> str:
    """« cite:2 » (source liée, rang 2), « nomme » (nommé sans lien), « absent », « » (non mesuré)."""
    def vrai(v) -> bool:
        return str(v or "").strip().lower() in ("true", "1", "oui", "yes", "x", "vrai", "o", "y")
    cite, nomme = str(ligne.get("cite") or "").strip(), str(ligne.get("nomme") or "").strip()
    if not cite and not nomme:
        return ""
    if vrai(cite):
        rang = int(_num(ligne.get("rang")) or 0)
        return f"cite:{rang}" if rang else "cite"
    return "nomme" if vrai(nomme) else "absent"


def present(etat: str) -> bool:
    return etat.startswith("cite") or etat == "nomme"


def lire_releves(fichiers: list[Path], mois: str, domaine: str = "") -> dict[str, dict]:
    """Relevés share_of_model (ou grille manuelle) → par prompt : état par moteur.

    Le relevé le plus récent du mois ou d'avant l'emporte. Un prompt jamais
    mesuré jusque-là prend le relevé du mois suivant (la routine mensuelle
    mesure le 1er du mois d'après). Les mesures sans web (notoriété) sont écartées.
    """
    def mois_du(f: Path) -> str:
        m = re.search(r"(\d{4}-\d{2})", f.name)
        return m.group(1) if m else ""
    fichiers = sorted((f for f in fichiers if "sans-web" not in f.name),
                      key=lambda f: (mois_du(f), f.stat().st_mtime if f.exists() else 0))
    avant = [f for f in fichiers if not mois_du(f) or mois_du(f) <= mois]
    suivant = [f for f in fichiers if mois_du(f) == rapport.decaler(mois, 1)]
    resultat = _releves(avant, domaine)
    for prompt, r in _releves(suivant, domaine).items():
        resultat.setdefault(prompt, r)
    return resultat


def _releves(fichiers: list[Path], domaine: str) -> dict[str, dict]:
    domaine = (domaine or "").lower().removeprefix("www.")
    resultat: dict[str, dict] = {}
    for f in fichiers:
        mesure = (re.search(r"(\d{4}-\d{2})", f.name) or [""])[0]
        with f.open(encoding="utf-8-sig", newline="") as fh:
            for l in csv.DictReader(fh):
                prompt = normaliser_requete(l.get("prompt", ""))
                moteur = ALIAS_MOTEURS.get(str(l.get("moteur", "")).strip().lower())
                etat = etat_ia(l)
                if not prompt or not moteur or not etat:
                    continue
                r = resultat.setdefault(prompt, {"mesure": "", "concurrent": "", "_nommes": Counter(),
                                                 "_sources": Counter()})
                r[moteur] = etat
                r["mesure"] = mesure or r["mesure"]
                r["_nommes"].update(c.strip() for c in str(l.get("concurrents_nommes") or "").split(",") if c.strip())
                if not present(etat):
                    r["_sources"].update(s.strip() for s in str(l.get("sources") or "").split(",")[:1]
                                         if s.strip() and not (domaine and s.strip().endswith(domaine)))
    # Le concurrent retenu : le plus nommé dans les réponses, à défaut la source la plus citée à la place du site.
    for r in resultat.values():
        nommes, sources = r.pop("_nommes"), r.pop("_sources")
        r["concurrent"] = (nommes or sources).most_common(1)[0][0] if (nommes or sources) else ""
    return resultat


def action_suggeree(r: dict) -> tuple[str, str]:
    """(valeur de la colonne Action du schéma Notion, libellé détaillé)."""
    if r.get("statut") == "a-creer":
        return "", "Créer la page : benchmark, brief, rédaction"
    if r.get("statut") == "en-cours":
        return "", "En cours : publier, puis journaliser"
    if r.get("en_mesure"):
        return "Garder / Maintenir", f"En cours de mesure jusqu'au {r['en_mesure']} : ne pas toucher"
    if not r.get("mot_cle_principal"):
        return "", "Choisir le mot-clé principal de la page"
    if not _num(r.get("impressions")):
        return "Vérifier indexation / Relancer", "Aucune impression ce mois-ci : vérifier l'indexation"
    pos, delta = _num(r.get("position_mc")), _num(r.get("delta_position_mc"))
    if pos is None:
        code, libelle = "Mettre à jour", "Absente sur son mot-clé principal : revoir l'angle, ou changer de mot-clé"
    elif delta is not None and delta <= -3:
        code, libelle = "Mettre à jour", f"Perd {_fr(-delta)} places : diagnostiquer avant de toucher (seo-traffic-drop)"
    elif pos <= 3:
        impr, ctr = _num(r.get("impressions_mc")) or 0, (_num(r.get("ctr_mc")) or 0) / 100
        if impr >= 100 and ctr < opportunites.ctr_attendu(pos) / 2:
            code, libelle = "Mettre à jour (quick win)", "Top 3 mais peu cliquée : réécrire title et meta"
        else:
            code, libelle = "Garder / Maintenir", "Tenir la place : fraîcheur et liens internes"
    elif pos <= 10:
        code, libelle = "Optimiser → top 3", "Page 1 : enrichir la page et son maillage pour viser le top 3"
    elif pos <= 20:
        code, libelle = "Mettre à jour (quick win)", "Page 2 : section manquante et liens internes pour passer en page 1"
    else:
        code, libelle = "Mettre à jour", "Au-delà de 20 : refondre la page ou revoir son mot-clé principal"
    if r.get("page_mieux_placee"):
        libelle += f" · une autre page est mieux placée ({chemin_de(r['page_mieux_placee'])}) : cannibalisation"
    etats = [r.get(f"ia_{m}", "") for m in MOTEURS]
    if any(etats) and not any(present(e) for e in etats) and r.get("funnel") in ("MOFU", "BOFU"):
        libelle += " · GEO : aucun moteur ne cite le site sur le prompt principal"
    return code, libelle


def construire_mois(cartographie: list[dict], pages: dict, pages_prec: dict, pq: dict, pq_prec: dict,
                    ia: dict, historique_prec: dict[str, dict], mois: str,
                    en_mesure: dict[str, str] | None = None) -> list[dict]:
    """Une ligne par page de la cartographie, pour le mois : page, page × mot-clé principal, IA, action.

    pages / pages_prec : indexer(lignes page) ; pq / pq_prec : indexer(lignes page × requête, True) ;
    ia : lire_releves() ; historique_prec : lignes de l'historique du mois précédent, par clé.
    """
    en_mesure = {normaliser_url(k): v for k, v in (en_mesure or {}).items()}
    par_requete: dict[str, list[tuple[str, dict]]] = {}
    for (page, requete), m in pq.items():
        par_requete.setdefault(requete, []).append((page, m))
    sortie = []
    for c in cartographie:
        url, cle = c.get("url", ""), cle_de(c)
        mc, prompt = normaliser_requete(c.get("mot_cle_principal", "")), c.get("prompt_principal", "")
        k = normaliser_url(url)
        p, pp = pages.get(k) if url else None, pages_prec.get(k) if url else None
        m, mp = (pq.get((k, mc)), pq_prec.get((k, mc))) if url and mc else (None, None)
        r = {"mois": mois, "cle": cle, "url": url, "mot_cle_principal": c.get("mot_cle_principal", ""),
             "prompt_principal": prompt, "statut": c.get("statut", ""), "funnel": c.get("funnel", ""),
             "priorite": c.get("priorite", ""), "prompt_a_valider": "prompt_principal" in drapeaux(c),
             "clics": p["clics"] if p else (0 if url else None), "impressions": p["impressions"] if p else (0 if url else None),
             "ctr": p["ctr"] if p else None, "position": p["position"] if p else None,
             "clics_prec": pp["clics"] if pp else None, "impressions_prec": pp["impressions"] if pp else None,
             "position_prec": pp["position"] if pp else None,
             "clics_mc": m["clics"] if m else None, "impressions_mc": m["impressions"] if m else None,
             "ctr_mc": m["ctr"] if m else None, "position_mc": m["position"] if m else None,
             "clics_mc_prec": mp["clics"] if mp else None, "position_mc_prec": mp["position"] if mp else None}
        r["delta_position_mc"] = round(mp["position"] - m["position"], 1) if m and mp and m["position"] and mp["position"] else None
        r["delta_clics_mc"] = (m["clics"] if m else 0) - (mp["clics"] if mp else 0) if (m or mp) else None
        # Une autre page du site mieux placée sur le mot-clé : la cannibalisation se voit dans les données.
        autres = [(pg, x) for pg, x in par_requete.get(mc, []) if pg != k and x["position"]] if mc else []
        meilleure = min(autres, key=lambda t: t[1]["position"], default=None)
        r["page_mieux_placee"] = meilleure[0] if meilleure and (not m or not m["position"]
                                                                or meilleure[1]["position"] < m["position"]) else ""
        mesure = ia.get(normaliser_requete(prompt), {}) if prompt else {}
        for moteur in MOTEURS:
            r[f"ia_{moteur}"] = mesure.get(moteur, "")
        r["ia_mesure"], r["ia_concurrent"] = mesure.get("mesure", ""), mesure.get("concurrent", "")
        avant = historique_prec.get(cle, {})
        evolution = []
        for moteur in MOTEURS:
            maintenant, hier = r[f"ia_{moteur}"], avant.get(f"ia_{moteur}", "")
            if maintenant and hier and present(maintenant) != present(hier):
                evolution.append(("+" if present(maintenant) else "-") + moteur)
        r["ia_evolution"] = " ".join(evolution)
        r["en_mesure"] = en_mesure.get(k, "") if url else ""
        r["action_notion"], r["action"] = action_suggeree(r)
        sortie.append(r)
    return sortie


def synthese(lignes: list[dict], n: int = 5) -> dict:
    """Résumé du mois : utilisé par le tableau du mois et par rapport.py (lignes de l'historique)."""
    def resume(l: dict) -> dict:
        return {"url": l.get("url", ""), "mot_cle_principal": l.get("mot_cle_principal", ""),
                "position_mc": _num(l.get("position_mc")), "position_mc_prec": _num(l.get("position_mc_prec")),
                "delta_position_mc": _num(l.get("delta_position_mc")), "prompt_principal": l.get("prompt_principal", ""),
                "ia_evolution": l.get("ia_evolution", "")}
    avec_delta = [l for l in lignes if _num(l.get("delta_position_mc")) is not None]
    hausses = sorted([l for l in avec_delta if _num(l["delta_position_mc"]) > 0], key=lambda l: -_num(l["delta_position_mc"]))
    baisses = sorted([l for l in avec_delta if _num(l["delta_position_mc"]) < 0], key=lambda l: _num(l["delta_position_mc"]))
    mesures = [l for l in lignes if any(l.get(f"ia_{m}") for m in MOTEURS)]
    presents = [l for l in mesures if any(present(l.get(f"ia_{m}", "")) for m in MOTEURS)]
    gagnes = [l for l in lignes if "+" in (l.get("ia_evolution") or "")]
    perdus = [l for l in lignes if re.search(r"(^|\s)-", l.get("ia_evolution") or "")]
    return {"pages": len([l for l in lignes if l.get("statut") != "a-creer"]),
            "a_creer": len([l for l in lignes if l.get("statut") == "a-creer"]),
            "en_hausse": len(hausses), "en_baisse": len(baisses),
            "top_10": len([l for l in lignes if (_num(l.get("position_mc")) or 99) <= 10]),
            "hausses": [resume(l) for l in hausses[:n]], "baisses": [resume(l) for l in baisses[:n]],
            "prompts_mesures": len(mesures), "prompts_presents": len(presents),
            "prompts_gagnes": [resume(l) for l in gagnes], "prompts_perdus": [resume(l) for l in perdus],
            "mesure_ia": max((l.get("ia_mesure") or "" for l in lignes), default="")}


# ─── Mensuel : sorties ────────────────────────────────────────────

def cellule(texte: str, maximum: int = 0) -> str:
    t = " ".join(str(texte or "").split()).replace("|", "\\|")
    return t[:maximum - 1] + "…" if maximum and len(t) > maximum else t


def case_ia(etat: str) -> str:
    if not etat:
        return "—"
    if etat.startswith("cite"):
        rang = etat.partition(":")[2]
        return f"✓ {rang}" if rang else "✓"
    return "nommé" if etat == "nomme" else "✗"


def evolution_lisible(evolution: str) -> str:
    morceaux = []
    for e in (evolution or "").split():
        nom = NOMS_MOTEURS.get(e[1:], e[1:])
        morceaux.append(f"gagné sur {nom}" if e.startswith("+") else f"perdu sur {nom}")
    return ", ".join(morceaux)


def markdown(res: dict) -> str:
    s, lignes = res["synthese"], res["lignes"]
    l = [f"# Cartographie — {res['projet']} — {res['mois']}", "",
         "> Chiffres calculés par `cartographie.py` depuis Search Console et les relevés IA. Ne pas les "
         "modifier à la main : relancer le script. Position et clics : ceux de la page **sur son mot-clé "
         "principal**. Δ = places gagnées depuis le mois précédent (positif = mieux). IA : ✓ rang = site cité "
         "en source, nommé = marque citée sans lien, ✗ = absent, — = prompt non mesuré.", "",
         f"**{s['pages']} page(s) suivie(s), {s['a_creer']} à créer · mot-clé principal : {s['en_hausse']} en hausse, "
         f"{s['en_baisse']} en baisse, {s['top_10']} en page 1 · prompts principaux : site présent sur "
         f"{s['prompts_presents']}/{s['prompts_mesures']} mesuré(s), {len(s['prompts_gagnes'])} gagné(s) et "
         f"{len(s['prompts_perdus'])} perdu(s) ce mois-ci" + (f" (relevé IA : {s['mesure_ia']})" if s["mesure_ia"] else " (aucun relevé IA)") + "**", ""]
    for mc, pages in res.get("cannibalisation", {}).items():
        l.append(f"⚠️ Cannibalisation : « {mc} » est le mot-clé principal de {len(pages)} pages ({', '.join(pages)}). "
                 "Un mot-clé, une page.")
    if res.get("cannibalisation"):
        l.append("")
    l += ["## Le tableau", "",
          "| Page | Mot-clé principal | Pos. M | Pos. M-1 | Δ | Clics (Δ) | Prompt principal | ChatGPT | Gemini | Claude "
          "| Action suggérée |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    ordre = {"P1": 0, "P2": 1, "P3": 2}
    for r in sorted(lignes, key=lambda r: (r["statut"] == "a-creer", ordre.get(r.get("priorite", ""), 3),
                                           -(r.get("impressions") or 0))):
        page = cellule(chemin_de(r["url"]), 45) if r["url"] else "*à créer*"
        clics = "—" if r["clics_mc"] is None and r["delta_clics_mc"] is None else \
            f"{r['clics_mc'] or 0} ({r['delta_clics_mc'] or 0:+d})"
        prompt = cellule(r["prompt_principal"], 80) + (" *(à valider)*" if r["prompt_a_valider"] and r["prompt_principal"] else "")
        l.append(f"| {page} | {cellule(r['mot_cle_principal'], 50) or '—'} | {_fr(r['position_mc'])} "
                 f"| {_fr(r['position_mc_prec'])} | {_fr(r['delta_position_mc'], signe=True)} | {clics} | {prompt or '—'} "
                 f"| {case_ia(r['ia_openai'])} | {case_ia(r['ia_gemini'])} | {case_ia(r['ia_claude'])} "
                 f"| {cellule(r['action'])} |")
    l.append("")
    for titre, bloc in (("Plus fortes hausses sur le mot-clé principal", s["hausses"]),
                        ("Plus fortes baisses sur le mot-clé principal", s["baisses"])):
        if bloc:
            l += [f"## {titre}", "", "| Page | Mot-clé principal | Position | Δ places |", "|---|---|---|---|"]
            l += [f"| {cellule(chemin_de(x['url']), 45)} | {cellule(x['mot_cle_principal'])} | "
                  f"{_fr(x['position_mc_prec'])} → {_fr(x['position_mc'])} | {_fr(x['delta_position_mc'], signe=True)} |"
                  for x in bloc]
            l.append("")
    if s["prompts_gagnes"] or s["prompts_perdus"]:
        l += ["## Prompts gagnés et perdus", ""]
        l += [f"- « {cellule(x['prompt_principal'])} » ({chemin_de(x['url']) if x['url'] else 'à créer'}) : "
              f"{evolution_lisible(x['ia_evolution'])}"
              for x in {(x["url"], x["prompt_principal"]): x for x in s["prompts_gagnes"] + s["prompts_perdus"]}.values()]
        l.append("")
    concurrents = Counter(r["ia_concurrent"] for r in lignes if r.get("ia_concurrent"))
    if concurrents:
        l += ["Cités à la place du site sur les prompts principaux : "
              + ", ".join(f"{c} ({n})" for c, n in concurrents.most_common(6)) + ".", ""]
    l += ["## Lecture et décisions", "",
          "<!-- À rédiger par l'agent : pourquoi les mots-clés principaux ont bougé, quels prompts viser le mois "
          "prochain, quelles lignes de la cartographie changer (avec le client). -->", ""]
    return "\n".join(l)


def ecrire_historique(chemin: Path, lignes: list[dict], mois: str) -> None:
    """Une ligne par page et par mois ; relancer le même mois remplace ses lignes."""
    anciennes = []
    if chemin.is_file():
        with chemin.open(encoding="utf-8", newline="") as f:
            anciennes = [l for l in csv.DictReader(f) if l.get("mois") != mois]
    nouvelles = [{c: ("" if r.get(c) is None else r.get(c)) for c in COLONNES_HISTORIQUE} for r in lignes]
    ecrire_csv(chemin, sorted(anciennes + nouvelles, key=lambda l: l["mois"]), COLONNES_HISTORIQUE)


def lire_historique(chemin: Path) -> list[dict]:
    if not chemin.is_file():
        return []
    with chemin.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def ecrire_markdown(cible: Path, texte: str) -> None:
    """Comme rapport.py : la section « Lecture et décisions » rédigée est conservée."""
    cible.parent.mkdir(parents=True, exist_ok=True)
    titre = "## Lecture et décisions"
    if cible.is_file():
        ancien = cible.read_text(encoding="utf-8")
        if titre in ancien:
            texte = texte[:texte.find(titre)] + ancien[ancien.find(titre):]
    cible.write_text(texte, encoding="utf-8")


def resume_pour_rapport(racine: Path, mois: str) -> dict | None:
    """Pour rapport.py : la synthèse du mois tirée de l'historique, None s'il n'y a rien."""
    lignes = [l for l in lire_historique(racine / HISTORIQUE) if l.get("mois") == mois]
    md = racine / "rapports" / f"cartographie-{mois}.md"
    if not lignes:
        return {"fichier": f"rapports/{md.name}", "pages": None} if md.is_file() else None
    return {"fichier": f"rapports/{md.name}" if md.is_file() else "", **synthese(lignes, n=3)}


# ─── Mensuel : collecte ───────────────────────────────────────────

def lire_gsc_mois(site: str, mois: str) -> tuple[list[dict], list[dict]]:
    import gsc
    debut, fin = rapport.bornes(mois)
    pages = [{"page": r["keys"][0], "clics": r["clicks"], "impressions": r["impressions"], "position": r["position"]}
             for r in gsc.requete(site, ["page"], debut, fin, 25000)]
    pq = [{"page": r["keys"][0], "requete": r["keys"][1], "clics": r["clicks"], "impressions": r["impressions"],
           "position": r["position"]} for r in gsc.requete(site, ["page", "query"], debut, fin, 100000)]
    return pages, pq


def fichiers_releves(racine: Path) -> list[Path]:
    motifs = ("releves-ia-*.csv", "donnees/ia-*.csv", "donnees/releves-ia-*.csv", "donnees/cartographie-ia-*.csv",
              "recherche/releves-ia-*.csv")
    return sorted({f for m in motifs for f in racine.glob(m)})


def rafraichir_volumes(lignes: list[dict]) -> float:
    """Volumes DataForSEO des mots-clés principaux, par langue. Renvoie le coût en $."""
    import demande
    cout = 0.0
    par_langue: dict[str, list[dict]] = {}
    for l in lignes:
        if l.get("mot_cle_principal"):
            par_langue.setdefault(l.get("langue") or langue_projet(), []).append(l)
    for langue, groupe in par_langue.items():
        lieu, code = demande.lieu_et_langue(argparse.Namespace(pays=None, lieu=None, langue=langue))
        mots = list(dict.fromkeys(normaliser_requete(l["mot_cle_principal"]) for l in groupe))[:1000]
        res, c = demande.appel("keywords_data/google_ads/search_volume/live",
                               [{"keywords": mots, "location_name": lieu, "language_code": code}])
        cout += c
        volumes = {normaliser_requete(r.get("keyword", "")): r.get("search_volume") or 0 for r in res}
        for l in groupe:
            v = volumes.get(normaliser_requete(l["mot_cle_principal"]))
            if v is not None:
                l["volume"] = str(v)
    return cout


def mesurer_prompts(lignes: list[dict], sortie: Path, moteurs_demandes: list[str] | None) -> int:
    """Interroge les moteurs IA sur les prompts principaux (payant). Même format que share_of_model."""
    marque, domaine = lire_valeur("projet.nom"), share_of_model.domaine_de(
        "https://" + re.sub(r"^https?://", "", lire_valeur("projet.domaine")))
    concurrents = lire_liste("projet.concurrents")
    prompts = list({normaliser_requete(l["prompt_principal"]): l for l in lignes if l.get("prompt_principal")}.values())
    moteurs = share_of_model.moteurs_disponibles(moteurs_demandes)
    if not moteurs or not prompts:
        print("  ! --prompts : aucun moteur IA configuré ou aucun prompt principal : rien mesuré", file=sys.stderr)
        return 0
    print(f"  {len(prompts)} prompt(s) × {len(moteurs)} moteur(s) ({', '.join(moteurs)}) = "
          f"{len(prompts) * len(moteurs)} appel(s) facturé(s) par les fournisseurs")
    releves = []
    for moteur in moteurs:
        for l in prompts:
            try:
                reponse = share_of_model.MOTEURS[moteur][1](l["prompt_principal"], web=True)
            except (share_of_model.ErreurMoteur, KeyError, IndexError) as exc:
                print(f"  {moteur:<10} ✗ {str(exc)[:80]}", file=sys.stderr)
                continue
            funnel = l.get("funnel", "")
            releves.append({"moteur": moteur, "famille": "visibilite", "funnel": funnel,
                            "poids": share_of_model.POIDS_FUNNEL.get(funnel, 1), "prompt": l["prompt_principal"],
                            **share_of_model.analyser(reponse, marque, domaine, concurrents)})
    if releves:
        ecrire_csv(sortie, releves, list(releves[0].keys()))
        print(f"  ✓ {sortie.name} · {len(releves)} relevé(s)")
    return len(releves)


def cmd_mensuel(a) -> int:
    racine = racine_projet()
    mois = a.mois or rapport.mois_precedent()
    if not re.fullmatch(r"\d{4}-\d{2}", mois):
        raise SystemExit("✗ --mois attend AAAA-MM")
    precedent = rapport.decaler(mois, -1)
    chemin = racine / FICHIER
    carto, entete = lire_cartographie(chemin)
    if not carto:
        print(f"✗ {FICHIER} vide ou absent : lancez d'abord « cartographie.py initialiser »", file=sys.stderr)
        return 1

    if a.csv:
        pq_l = opportunites.lire_csv_gsc(Path(a.csv))
        pq_p = opportunites.lire_csv_gsc(Path(a.csv_precedent)) if a.csv_precedent else []
        pages_l, pages_p, source = pq_l, pq_p, f"export {Path(a.csv).name}"
    else:
        try:
            import gsc
            site = a.site or gsc.site_par_defaut()
            pages_l, pq_l = lire_gsc_mois(site, mois)
            pages_p, pq_p = lire_gsc_mois(site, precedent)
            source = "Search Console"
        except Exception as exc:  # ErreurGSC, réseau
            print(f"✗ Search Console indisponible : {exc}\n  → exportez Performances (requêtes × pages) du mois "
                  "et relancez avec --csv (et --csv-precedent)", file=sys.stderr)
            return 1

    if a.volumes:
        try:
            cout = rafraichir_volumes(carto)
            ecrire_csv(chemin, carto, entete)
            print(f"  ✓ volumes rafraîchis · coût DataForSEO : {cout:.4f} $")
        except Exception as exc:  # identifiants absents, API
            print(f"  ! volumes non rafraîchis : {str(exc)[:120]}", file=sys.stderr)
    if a.prompts:
        mesurer_prompts(carto, racine / "donnees" / f"cartographie-ia-{mois}.csv",
                        [m.strip() for m in a.moteurs.split(",") if m.strip()] or None)

    fichiers = [Path(a.releves)] if a.releves else fichiers_releves(racine)
    ia = lire_releves(fichiers, mois, share_of_model.domaine_de("https://" + re.sub(r"^https?://", "", lire_valeur("projet.domaine"))))
    hist_prec = {l["cle"]: l for l in lire_historique(racine / HISTORIQUE) if l.get("mois") == precedent}
    delai = int(lire_valeur("mesure.delai_jours", "28") or 28)
    lignes = construire_mois(carto, indexer(pages_l), indexer(pages_p), indexer(pq_l, True), indexer(pq_p, True),
                             ia, hist_prec, mois, opportunites.pages_en_mesure(delai))
    res = {"projet": lire_valeur("projet.nom", racine.name), "mois": mois, "mois_precedent": precedent,
           "source": source, "synthese": synthese(lignes), "cannibalisation": doublons(carto), "lignes": lignes}
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return 0
    ecrire_historique(racine / HISTORIQUE, lignes, mois)
    dossier = racine / "rapports"
    ecrire_markdown(dossier / f"cartographie-{mois}.md", markdown(res))
    (dossier / f"cartographie-{mois}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n",
                                                       encoding="utf-8")
    s = res["synthese"]
    print(f"  ✓ rapports/cartographie-{mois}.md et .json · {HISTORIQUE}")
    print(f"  {s['pages']} page(s) · {s['en_hausse']} en hausse, {s['en_baisse']} en baisse sur leur mot-clé · "
          f"prompts : site présent sur {s['prompts_presents']}/{s['prompts_mesures']}")
    if not s["prompts_mesures"]:
        print("  ! aucun relevé IA trouvé : share_of_model.py sur recherche/prompts-ia.csv, ou --prompts")
    return 0


# ─── Exporter ─────────────────────────────────────────────────────

COLONNES_NOTION = ["Mot clé", "Statut", "Type", "Format", "Silo", "Cluster", "Priorité", "Potentiel business", "Canal",
                   "Intention", "Volume", "KD", "AI Overview", "Effort", "Action", "Position", "CTR", "Impressions",
                   "Clics", "Évolution position", "Dernière MAJ", "Slug", "Dans inventaire",
                   "URL", "Prompt principal", "Mots-clés secondaires", "Funnel", "ChatGPT", "Gemini", "Claude",
                   "Perplexity", "À valider"]
STATUT_NOTION = {"existante": "Existant", "a-creer": "À créer", "en-cours": "En cours", "publiee": "Publié"}
TYPE_NOTION = {"lead-magnet": "lead magnet"}


def ia_notion(etat: str) -> str:
    if not etat:
        return ""
    if etat.startswith("cite"):
        rang = etat.partition(":")[2]
        return f"cité (rang {rang})" if rang else "cité"
    return "nommé" if etat == "nomme" else "absent"


def lignes_notion(cartographie: list[dict], mesures: dict[str, dict]) -> list[dict]:
    """Une ligne Notion par ligne de la cartographie, avec les chiffres du dernier mois de l'historique."""
    sortie = []
    for c in cartographie:
        m = mesures.get(cle_de(c), {})
        chemin = chemin_de(c["url"]) if c.get("url") else ""
        sortie.append({
            "Mot clé": c.get("mot_cle_principal") or chemin, "Statut": STATUT_NOTION.get(c.get("statut", ""), ""),
            "Type": TYPE_NOTION.get(c.get("type", ""), c.get("type", "")),
            "Format": "Article" if c.get("type") == "article" else ("Page" if c.get("type") else ""),
            "Silo": c.get("silo", ""), "Cluster": c.get("cluster", ""), "Priorité": c.get("priorite", ""),
            "Potentiel business": "", "Canal": "SEO, GEO" if c.get("prompt_principal") else "SEO",
            "Intention": (c.get("intention") or "").capitalize(), "Volume": c.get("volume", ""), "KD": c.get("kd", ""),
            "AI Overview": "", "Effort": "", "Action": m.get("action_notion", ""),
            "Position": m.get("position_mc", ""), "CTR": m.get("ctr_mc", ""), "Impressions": m.get("impressions_mc", ""),
            "Clics": m.get("clics_mc", ""), "Évolution position": m.get("delta_position_mc", ""),
            "Dernière MAJ": c.get("derniere_maj", ""), "Slug": chemin,
            "Dans inventaire": "Yes" if c.get("statut") in ("existante", "publiee") else "No",
            "URL": c.get("url", ""), "Prompt principal": c.get("prompt_principal", ""),
            "Mots-clés secondaires": c.get("mots_cles_secondaires", ""), "Funnel": c.get("funnel", ""),
            **{NOMS_MOTEURS[mo]: ia_notion(m.get(f"ia_{mo}", "")) for mo in MOTEURS},
            "À valider": ", ".join(d.replace("mot_cle_principal", "mot-clé").replace("prompt_principal", "prompt")
                                   for d in drapeaux(c))})
    return sortie


def cmd_exporter(a) -> int:
    racine = racine_projet()
    carto, _ = lire_cartographie(racine / FICHIER)
    if not carto:
        print(f"✗ {FICHIER} vide ou absent", file=sys.stderr)
        return 1
    historique = lire_historique(racine / HISTORIQUE)
    mois = a.mois or max((l["mois"] for l in historique), default="")
    mesures = {l["cle"]: l for l in historique if l.get("mois") == mois}
    lignes = lignes_notion(carto, mesures)
    if a.json:
        print(json.dumps({"mois": mois, "colonnes": COLONNES_NOTION, "lignes": lignes}, ensure_ascii=False, indent=1))
        return 0
    cible = Path(a.notion_csv) if a.notion_csv else racine / "rapports" / "cartographie-notion.csv"
    cible.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig : Notion l'accepte, et Excel affiche enfin les accents.
    with cible.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES_NOTION)
        w.writeheader()
        w.writerows(lignes)
    print(f"  ✓ {cible} · {len(lignes)} ligne(s)" + (f", chiffres de {mois}" if mois else ", sans chiffres mensuels"))
    return 0


def main() -> int:
    charger_env()
    ap = argparse.ArgumentParser(description="Cartographie : un mot-clé principal et un prompt principal par page")
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("initialiser", help="créer ou compléter memoire/cartographie.csv (jamais d'écrasement)")
    p.add_argument("--site", help="propriété Search Console (défaut : config du projet)")
    p.add_argument("--jours", type=int, default=90)
    p.add_argument("--csv", help="export Search Console requête × page, à la place de l'API")
    p.add_argument("--impressions-min", type=int, default=10, help="sur la période, pour retenir une page")
    p.add_argument("--sitemap", help="URL du sitemap (défaut : https://<domaine>/sitemap.xml)")
    p.add_argument("--sans-sitemap", action="store_true")
    p.add_argument("--sitemap-max", type=int, default=500)
    p.add_argument("--categorie", default="", help="catégorie en toutes lettres, pour les prompts MOFU/BOFU")
    p.add_argument("--dry-run", action="store_true", help="afficher le bilan sans écrire")
    p.set_defaults(f=cmd_initialiser)

    p = sp.add_parser("mensuel", help="chiffres du mois → historique et rapports/cartographie-AAAA-MM.md")
    p.add_argument("--mois", help="AAAA-MM (défaut : mois précédent)")
    p.add_argument("--site")
    p.add_argument("--csv", help="export requête × page du mois, si l'API est indisponible")
    p.add_argument("--csv-precedent", help="même export pour le mois précédent")
    p.add_argument("--volumes", action="store_true", help="rafraîchir les volumes par DataForSEO (payant)")
    p.add_argument("--prompts", action="store_true", help="interroger les moteurs IA sur les prompts (payant)")
    p.add_argument("--moteurs", default="", help="avec --prompts : ex. openai,gemini (défaut : ceux qui ont une clé)")
    p.add_argument("--releves", help="fichier de relevés share_of_model à utiliser (défaut : le plus récent)")
    p.add_argument("--json", action="store_true", help="afficher le JSON sans rien écrire")
    p.set_defaults(f=cmd_mensuel)

    p = sp.add_parser("verifier", help="cannibalisation, lignes à valider, prompts hors règles")
    p.set_defaults(f=cmd_verifier)

    p = sp.add_parser("exporter", help="CSV aux colonnes du schéma Notion")
    p.add_argument("--notion-csv", nargs="?", const="", default="", metavar="FICHIER",
                   help="défaut : rapports/cartographie-notion.csv")
    p.add_argument("--mois", help="mois de l'historique à reprendre (défaut : le dernier)")
    p.add_argument("--json", action="store_true", help="lignes en JSON, pour une synchronisation par le MCP Notion")
    p.set_defaults(f=cmd_exporter)

    a = ap.parse_args()
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
