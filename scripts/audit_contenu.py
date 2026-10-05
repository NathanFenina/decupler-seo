#!/usr/bin/env python3
"""Audit de contenu : un verdict et une action pour chaque page publiée.

    python3 audit_contenu.py                                  # carte + Search Console en direct
    python3 audit_contenu.py --carte donnees/carte-contenu.csv --gsc gsc-pages.json
    python3 audit_contenu.py --obsolete "gpt-?3\\.5::GPT-3.5" --obsolete "windows 7::OS en fin de vie"
    python3 audit_contenu.py --json

Croise, pour chaque contenu de la carte (wp.py carte, ou tout CSV avec au
moins les colonnes url et nb_mots) :
  - Search Console sur 180 jours : impressions, clics, position ;
  - le nombre de mots et la date de dernière modification ;
  - des signaux d'obsolescence : une année passée dans le title, le H1, un
    H2 ou la meta (« Guide 2023 »), et les motifs propres au site (--obsolete
    ou `audit_contenu.obsolete` dans la config du projet) ;
  - les pages techniques (panier, compte, connexion…), à neutraliser et non
    à juger sur leur trafic.

Verdicts : vide · morte · périmée · mince · à pousser · saine · technique.
Le verdict est une proposition : la décision reste humaine, et rien n'est
modifié. Sortie : <sortie>/audit-contenu.md et audit-contenu.json.

Search Console, la première source trouvée gagne : --gsc (le JSON de
`gsc.py perf --par page --json`, ou un export CSV de l'interface), sinon
l'API en direct si des identifiants sont présents. Sans aucune des deux,
l'audit tourne en dégradé — sur la longueur et l'âge seulement — et le dit.

Bibliothèque standard uniquement.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import lire_liste, racine_projet  # noqa: E402

# Seuils. Volontairement simples et lisibles : un client doit pouvoir
# refaire le calcul à la main et contester un verdict.
MOTS_VIDE = 80
MOTS_MINCE = 400
AGE_MORTE_JOURS = 180         # une page de moins de six mois n'a pas encore eu sa chance
POSITION_POUSSER = (8.0, 20.0)
IMPRESSIONS_POUSSER = 100
JOURS_GSC = 180

ORDRE = ["technique", "vide", "morte", "périmée", "mince", "à pousser", "saine"]
ACTIONS = {
    "technique": "Vérifier noindex et absence du sitemap ; si c'est déjà le cas, ne rien faire",
    "vide": "Supprimer (410) si c'est un reste technique, sinon rediriger (301) vers la page la plus proche",
    "morte": "Rediriger (301) vers la page qui couvre le sujet, ou fusionner son contenu utile",
    "périmée+trafic": "Mettre à jour (versions, dates, captures, chiffres) : elle reçoit encore du trafic",
    "périmée": "Mettre à jour ou fusionner",
    "mince": "Enrichir : Google la montre, mais elle n'a pas la matière (sections manquantes)",
    "à pousser": "Quick win : title, sections manquantes, liens internes",
    "saine": "Garder",
}

# Pages sans contenu par nature : les juger sur leur trafic produirait des
# « vides » à supprimer qui casseraient le site.
TECHNIQUES = re.compile(
    r"/(panier|cart|commande|checkout|commander|mon-compte|my-account|compte|connexion|login|"
    r"inscription|register|mot-de-passe|lost-password|wishlist|liste-de-souhaits|merci|thank-you|"
    r"recherche|search|feed|wp-json)(/|$)", re.I)

ANNEE = re.compile(r"(?<!\d)(20\d\d)(?!\d)")


class ErreurAudit(Exception):
    """Erreur présentable telle quelle."""


# ═══════════════════════════════════════════════════════════════════
# Fonctions pures — testées hors ligne
# ═══════════════════════════════════════════════════════════════════

def cle_url(url: str) -> str:
    """Chemin seul, sans barre finale ni paramètres : clé commune carte ↔ Search Console."""
    chemin = urlparse(url.strip()).path if "://" in url else url.split("?")[0].split("#")[0]
    return chemin.strip("/").lower()


def _normaliser(nom: str) -> str:
    nom = unicodedata.normalize("NFKD", nom.strip().lower())
    return "".join(c for c in nom if not unicodedata.combining(c))


def _nombre(valeur) -> float:
    if valeur is None or valeur == "":
        return 0.0
    if isinstance(valeur, (int, float)):
        return float(valeur)
    brut = str(valeur).replace(" ", "").replace(" ", "").replace("%", "").replace(",", ".")
    try:
        return float(brut)
    except ValueError:
        return 0.0


def lire_gsc_json(donnees: dict | list) -> dict[str, dict]:
    """Le JSON de `gsc.py perf --par page --json` (ou une liste de lignes)."""
    lignes = donnees.get("rows", []) if isinstance(donnees, dict) else donnees
    perf = {}
    for r in lignes:
        url = (r.get("keys") or [r.get("page") or r.get("url") or ""])[0]
        if not url:
            continue
        perf[cle_url(url)] = {"impressions": int(_nombre(r.get("impressions"))),
                              "clics": int(_nombre(r.get("clicks", r.get("clics")))),
                              "position": round(_nombre(r.get("position")), 1) or None}
    return perf


def lire_gsc_csv(texte: str) -> dict[str, dict]:
    """Un export CSV de l'interface Search Console (onglet Pages), en français ou en anglais."""
    lecteur = csv.DictReader(texte.splitlines())
    colonnes = {_normaliser(c): c for c in (lecteur.fieldnames or [])}

    def trouver(*noms: str) -> str | None:
        for nom in noms:
            for norme, brut in colonnes.items():
                if nom in norme:
                    return brut
        return None

    c_url = trouver("page", "url", "adresse")
    if not c_url:
        raise ErreurAudit("Export Search Console sans colonne page ou URL.")
    c_imp, c_clic, c_pos = trouver("impression"), trouver("clic", "click"), trouver("position")
    perf = {}
    for r in lecteur:
        if not r.get(c_url):
            continue
        perf[cle_url(r[c_url])] = {"impressions": int(_nombre(r.get(c_imp))) if c_imp else 0,
                                   "clics": int(_nombre(r.get(c_clic))) if c_clic else 0,
                                   "position": round(_nombre(r.get(c_pos)), 1) or None if c_pos else None}
    return perf


def compiler_obsoletes(motifs: list[str]) -> list[tuple[re.Pattern, str]]:
    """« expression::libellé » → (motif compilé, libellé). Sans libellé, le motif sert de libellé.

    « :: » plutôt que « | » : la barre verticale appartient aux expressions
    régulières (« gpt-?3\\.5|gpt-4o »).
    """
    compiles = []
    for brut in motifs:
        motif, _, libelle = brut.partition("::")
        try:
            compiles.append((re.compile(motif, re.I), libelle.strip() or motif))
        except re.error as exc:
            print(f"  ! motif ignoré, expression invalide « {motif} » : {exc}", file=sys.stderr)
    return compiles


def signaux_obsolescence(ligne: dict, annee_courante: int,
                         motifs: list[tuple[re.Pattern, str]] | None = None) -> list[str]:
    """Années passées dans les zones affichées (title, H1, H2, meta), puis motifs du site.

    Une année dans le corps du texte n'est pas un signal : « étude de 2021 »
    est souvent juste. Une année dans un titre promet de l'actualité.
    """
    vitrine = " ".join(str(ligne.get(c) or "") for c in ("titre", "meta_titre", "h1", "h2", "meta_description"))
    signaux = sorted({f"titre daté {a}" for a in ANNEE.findall(vitrine) if int(a) < annee_courante})
    tout = vitrine + " " + str(ligne.get("termes") or "")
    for motif, libelle in motifs or []:
        if motif.search(tout) and libelle not in signaux:
            signaux.append(libelle)
    return signaux


def verdict(p: dict) -> tuple[str, str]:
    """Règles dans l'ordre : la première qui s'applique gagne."""
    if p.get("technique"):
        return "technique", ACTIONS["technique"]
    imp, pos, mots, age = p["impressions"], p["position"], p["mots"], p["age_jours"]
    gsc = p.get("gsc", True)
    if mots < MOTS_VIDE and (imp == 0 or not gsc):
        return "vide", ACTIONS["vide"]
    if gsc and imp == 0 and age is not None and age > AGE_MORTE_JOURS:
        return "morte", ACTIONS["morte"]
    if p["obsolete"]:
        return "périmée", ACTIONS["périmée+trafic" if imp > 0 else "périmée"]
    if pos and POSITION_POUSSER[0] <= pos <= POSITION_POUSSER[1] and imp >= IMPRESSIONS_POUSSER:
        return "à pousser", ACTIONS["à pousser"]
    if mots < MOTS_MINCE and (imp > 0 or not gsc):
        return "mince", ACTIONS["mince"]
    return "saine", ACTIONS["saine"]


def auditer(carte: list[dict], perf: dict[str, dict] | None, aujourdhui: dt.date,
            motifs: list[tuple[re.Pattern, str]] | None = None) -> list[dict]:
    resultats = []
    for ligne in carte:
        url = ligne.get("url") or ""
        if not url or (ligne.get("statut") and ligne["statut"] != "publish"):
            continue
        g = (perf or {}).get(cle_url(url), {})
        modifie = (ligne.get("modifie") or "")[:10]
        try:
            age = (aujourdhui - dt.date.fromisoformat(modifie)).days
        except ValueError:
            age = None
        p = {
            "url": url, "titre": ligne.get("titre") or "",
            "impressions": g.get("impressions", 0), "clics": g.get("clics", 0),
            "position": g.get("position"), "mots": int(_nombre(ligne.get("nb_mots"))),
            "modifie": modifie, "age_jours": age,
            "liens_entrants": int(_nombre(ligne.get("liens_entrants"))) if ligne.get("liens_entrants") not in (None, "") else None,
            "obsolete": signaux_obsolescence(ligne, aujourdhui.year, motifs),
            "technique": bool(TECHNIQUES.search(urlparse(url).path or url)),
            "gsc": perf is not None,
        }
        p["verdict"], p["action"] = verdict(p)
        resultats.append(p)
    resultats.sort(key=lambda p: (ORDRE.index(p["verdict"]), -p["impressions"], p["url"]))
    return resultats


SANS_GSC = ("**Sans Search Console** : verdicts fondés sur la longueur et l'âge seulement — "
            "« morte » et « à pousser » ne peuvent pas être établis.")


def rendre_markdown(res: list[dict], source: str, aujourdhui: dt.date) -> str:
    """`source` : la phrase qui dit d'où viennent les chiffres (période, fichier, ou SANS_GSC)."""
    compte = {v: sum(1 for p in res if p["verdict"] == v) for v in ORDRE}
    md = [f"# Audit de contenu — {aujourdhui.isoformat()}", "", f"{source} {len(res)} contenus publiés.", "",
          " · ".join(f"**{v}** : {n}" for v, n in compte.items() if n), ""]
    rentables = [p for p in res if p["verdict"] in ("périmée", "mince", "à pousser") and p["impressions"] > 0]
    if rentables:
        md += ["## Les 5 actions les plus rentables", "",
               "Celles qui ont déjà des impressions : le travail porte tout de suite.", ""]
        for p in sorted(rentables, key=lambda p: -p["impressions"])[:5]:
            md.append(f"1. `{p['url']}` — {p['verdict']}, {p['impressions']} impressions : {p['action']}")
        md.append("")
    for v in ORDRE[:-1]:
        lot = [p for p in res if p["verdict"] == v]
        if not lot:
            continue
        md += [f"## {v.capitalize()} ({len(lot)})", "",
               "| Page | Impr. | Clics | Pos. | Mots | Modifiée | Signaux | Action |",
               "|---|---:|---:|---:|---:|---|---|---|"]
        for p in lot:
            md.append(f"| {p['url']} | {p['impressions']} | {p['clics']} | {p['position'] or '—'} | {p['mots']} | "
                      f"{p['modifie'] or '—'} | {', '.join(p['obsolete'])} | {p['action']} |")
        md.append("")
    return "\n".join(md)


# ═══════════════════════════════════════════════════════════════════
# Entrées et sorties
# ═══════════════════════════════════════════════════════════════════

def chemin(c: str) -> Path:
    p = Path(c)
    return p if p.is_absolute() else racine_projet() / p


def lire_carte(fichier: Path) -> list[dict]:
    if not fichier.is_file():
        raise ErreurAudit(f"Carte introuvable ({fichier}). Lancez d'abord : wp.py carte "
                          "(ou fournissez un CSV avec les colonnes url et nb_mots).")
    with open(fichier, newline="", encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))
    if lignes and not {"url", "nb_mots"} <= set(lignes[0]):
        raise ErreurAudit("La carte doit contenir au moins les colonnes url et nb_mots.")
    return lignes


def lire_gsc_fichier(fichier: Path) -> dict[str, dict]:
    texte = fichier.read_text(encoding="utf-8-sig")
    if texte.lstrip().startswith(("{", "[")):
        return lire_gsc_json(json.loads(texte))
    return lire_gsc_csv(texte)


def gsc_en_direct(jours: int, site: str | None) -> tuple[dict[str, dict], tuple[str, str]] | None:
    import gsc  # import tardif : l'audit doit tourner sans Search Console
    if not gsc.identifiants_presents():
        return None
    debut, fin = gsc.fenetre(jours)
    lignes = gsc.requete(site or gsc.site_par_defaut(), ["page"], debut, fin, 25000)
    return lire_gsc_json(lignes), (debut, fin)


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit de contenu : un verdict et une action par page")
    ap.add_argument("--carte", default="donnees/carte-contenu.csv", help="CSV de wp.py carte (url, nb_mots…)")
    ap.add_argument("--gsc", help="JSON de gsc.py perf --par page --json, ou export CSV de l'interface")
    ap.add_argument("--site", help="propriété Search Console, pour la lecture en direct")
    ap.add_argument("--jours", type=int, default=JOURS_GSC)
    ap.add_argument("--obsolete", action="append", default=[],
                    help="« expression::libellé » qui date un contenu (répétable)")
    ap.add_argument("--sortie", default="donnees", help="dossier de sortie (audit-contenu.md et .json)")
    ap.add_argument("--aujourdhui", help=argparse.SUPPRESS)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    aujourdhui = dt.date.fromisoformat(a.aujourdhui) if a.aujourdhui else dt.date.today()
    try:
        carte = lire_carte(chemin(a.carte))
    except (ErreurAudit, OSError) as exc:
        print(f"  ✗ {exc}", file=sys.stderr)
        return 1

    perf, source = None, SANS_GSC
    try:
        if a.gsc:
            perf = lire_gsc_fichier(chemin(a.gsc))
            source = f"Search Console : export `{a.gsc}`."
        elif direct := gsc_en_direct(a.jours, a.site):
            perf, (debut, fin) = direct
            source = f"Search Console du {debut} au {fin} ({a.jours} jours)."
    except (ErreurAudit, json.JSONDecodeError, OSError) as exc:
        print(f"  ✗ {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # une panne de l'API ne doit pas empêcher l'audit dégradé
        print(f"  ! Search Console indisponible ({exc}) : audit en dégradé.", file=sys.stderr)

    motifs = compiler_obsoletes(a.obsolete + lire_liste("audit_contenu.obsolete"))
    res = auditer(carte, perf, aujourdhui, motifs)

    sortie = chemin(a.sortie)
    sortie.mkdir(parents=True, exist_ok=True)
    doc = {"date": aujourdhui.isoformat(), "source": source, "gsc": perf is not None, "pages": res}
    (sortie / "audit-contenu.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    md = rendre_markdown(res, source, aujourdhui)
    (sortie / "audit-contenu.md").write_text(md, encoding="utf-8")

    if a.json:
        print(json.dumps(doc, ensure_ascii=False, indent=1))
    else:
        print("\n".join(md.splitlines()[:6]))
        print(f"\n  → {sortie / 'audit-contenu.md'}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
