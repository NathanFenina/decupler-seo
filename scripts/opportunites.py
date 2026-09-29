#!/usr/bin/env python3
"""Classement des opportunités SEO d'un client — où agir d'abord, et quoi faire.

    python3 opportunites.py                              # Search Console, 90 jours
    python3 opportunites.py --jours 28 --top 40
    python3 opportunites.py --csv export-gsc.csv         # export requête × page
    python3 opportunites.py --demande mots-cles.csv      # requete,volume[,page] : la demande où le site n'apparaît pas
    python3 opportunites.py --ecrire                     # → rapports/opportunites-AAAA-MM-JJ.md

Le moteur est le même pour tous les clients ; ce qui change, c'est le
**lexique** du projet, `memoire/lexique.csv` : les thèmes de son métier, la
valeur de chacun pour son chiffre d'affaires (1 à 3), et les motifs qui les
reconnaissent, dans toutes ses langues.

    theme,valeur,motif
    creation-societe,3,cr[ée]+er? (une )?(soci[ée]t[ée]|entreprise)
    creation-societe,3,company (formation|setup)
    creation-societe,3,إنشاء شركة
    depot-marque,2,(d[ée]p[ôo]t|enregistr\\w*) (de )?marque

Score = clics mensuels gagnables × valeur du thème × facilité.
- Clics gagnables : impressions × (CTR attendu à la position visée − CTR actuel).
- Facilité : un title à réécrire est plus sûr qu'une page à faire monter de
  la 2e page, elle-même plus sûre qu'une page à créer.
- Les pages en cours de mesure (modifiées il y a moins de `mesure.delai_jours`
  dans le journal) sont signalées et exclues : les toucher fausserait la
  mesure de la modification précédente.
- Les requêtes de marque sont comptées à part : elles ne sont pas une
  opportunité, elles sont déjà acquises.

Sans dépendance.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import charger_env, lire_liste, lire_valeur, racine_projet  # noqa: E402

# CTR organique moyen par position, ordre de grandeur des études publiques
# récentes, AI Overviews compris. Il sert à comparer des opportunités entre
# elles, pas à prédire un trafic au clic près.
CTR_ATTENDU = {1: 0.28, 2: 0.16, 3: 0.11, 4: 0.08, 5: 0.06, 6: 0.045, 7: 0.035, 8: 0.03, 9: 0.025, 10: 0.02}

ACTIONS = {
    # type : (libellé, facilité, type du journal)
    "ctr": ("Réécrire title et meta : la page est bien placée mais peu cliquée", 1.0, "title"),
    "page-1": ("Enrichir la page et son maillage pour gagner des places en page 1", 0.8, "contenu"),
    "page-2": ("Renforcer la page (section manquante, liens internes) pour passer en page 1", 0.5, "reecriture-section"),
    "cannibalisation": ("Consolider : plusieurs pages se disputent la requête", 0.6, "contenu"),
    "loin": ("Créer une page dédiée ou refondre : le site n'est pas en position de gagner", 0.25, "page-neuve"),
    "a-creer": ("Créer une page : demande réelle, le site n'y apparaît pas", 0.25, "page-neuve"),
    "invisible": ("Page publiée mais absente des résultats : revoir l'angle, le maillage, les liens", 0.35, "contenu"),
    "a-verifier": ("Page publiée, position inconnue sans Search Console : vérifier puis renforcer", 0.35, "contenu"),
}


def ctr_attendu(position: float) -> float:
    p = max(1, round(position))
    if p <= 10:
        return CTR_ATTENDU[p]
    return 0.01 if p <= 20 else 0.003


# ─── Le lexique du projet ─────────────────────────────────────────

def lire_lexique(chemin: Path) -> list[tuple[str, int, re.Pattern]]:
    if not chemin.is_file():
        return []
    lexique = []
    with chemin.open(encoding="utf-8") as f:
        for ligne in csv.DictReader(f):
            motif = (ligne.get("motif") or "").strip()
            if not motif or (ligne.get("theme") or "").startswith("#"):
                continue
            try:
                lexique.append((ligne["theme"].strip(), int(ligne.get("valeur") or 1), re.compile(motif, re.I)))
            except (re.error, ValueError) as exc:
                print(f"  ! lexique : ligne ignorée ({motif}) : {exc}", file=sys.stderr)
    return lexique


def theme_de(requete: str, lexique: list) -> tuple[str, int]:
    for theme, valeur, motif in lexique:
        if motif.search(requete):
            return theme, valeur
    return "hors-lexique", 1


def motifs_marque() -> list[re.Pattern]:
    termes = lire_liste("opportunites.marque")
    if not termes:
        # Par défaut : le nom du projet et le nom du domaine (« atlas-conseil » pour atlas-conseil.fr).
        hote = re.sub(r"^(https?://)?(www\.)?", "", lire_valeur("projet.domaine")).split("/")[0]
        termes = [lire_valeur("projet.nom"), hote.split(".")[0] if hote else ""]
    return [re.compile(re.escape(t.strip()), re.I) for t in termes if t and len(t.strip()) >= 3]


# ─── Les données ──────────────────────────────────────────────────

def _nombre(v) -> float:
    try:
        return float(str(v).replace("%", "").replace(",", ".").replace(" ", "").replace(" ", ""))
    except ValueError:
        return 0.0


COLONNES = {"requete": ("query", "requête", "requete", "requêtes les plus fréquentes", "top queries", "keys"),
            "page": ("page", "pages", "url", "landing page", "pages les plus populaires", "top pages"),
            "clics": ("clicks", "clics"), "impressions": ("impressions",), "position": ("position",)}


def lire_csv_gsc(chemin: Path) -> list[dict]:
    with chemin.open(encoding="utf-8-sig") as f:
        lecteur = csv.DictReader(f)
        correspondance = {}
        for col in lecteur.fieldnames or []:
            for cle, noms in COLONNES.items():
                if col.strip().lower() in noms:
                    correspondance[cle] = col
        if "requete" not in correspondance:
            raise SystemExit(f"✗ {chemin} : colonne de requête introuvable ({', '.join(lecteur.fieldnames or [])})")
        return [{"requete": l[correspondance["requete"]].strip(),
                 "page": l.get(correspondance.get("page", ""), "") or "",
                 "clics": _nombre(l.get(correspondance.get("clics", ""), 0)),
                 "impressions": _nombre(l.get(correspondance.get("impressions", ""), 0)),
                 "position": _nombre(l.get(correspondance.get("position", ""), 0))}
                for l in lecteur if l.get(correspondance["requete"])]


def lire_gsc(jours: int, site: str | None) -> list[dict]:
    import gsc
    site = site or gsc.site_par_defaut()
    debut, fin = gsc.fenetre(jours)
    return [{"requete": r["keys"][0], "page": r["keys"][1], "clics": r["clicks"],
             "impressions": r["impressions"], "position": r["position"]}
            for r in gsc.requete(site, ["query", "page"], debut, fin, 25000)]


def lire_demande(chemin: Path) -> dict[str, tuple[float, str]]:
    """requête → (volume mensuel, page qui la vise si elle existe déjà)."""
    with chemin.open(encoding="utf-8-sig") as f:
        lecteur = csv.DictReader(f)
        cols = {c.lower().strip(): c for c in lecteur.fieldnames or []}
        c_req = next((cols[c] for c in ("requete", "requête", "keyword", "mot-clé", "mot_cle", "query") if c in cols), None)
        c_vol = next((cols[c] for c in ("volume", "search volume", "volume de recherche", "search_volume") if c in cols), None)
        if not c_req or not c_vol:
            raise SystemExit(f"✗ {chemin} : colonnes attendues « requete » et « volume »")
        c_page = next((cols[c] for c in ("page", "url") if c in cols), None)
        return {l[c_req].strip().lower(): (_nombre(l[c_vol]), (l.get(c_page) or "").strip() if c_page else "")
                for l in lecteur if l.get(c_req)}


def pages_en_mesure(delai: int) -> dict[str, str]:
    """URL modifiées depuis moins de `delai` jours et pas encore jugées → date de fin de mesure."""
    journal = racine_projet() / "journal" / "modifications.csv"
    if not journal.is_file():
        return {}
    limite = dt.date.today() - dt.timedelta(days=delai)
    en_mesure = {}
    with journal.open(encoding="utf-8") as f:
        for l in csv.DictReader(f):
            try:
                jour = dt.date.fromisoformat(l.get("date", "")[:10])
            except ValueError:
                continue
            if jour > limite and not l.get("verdict"):
                en_mesure[normaliser(l.get("url", ""))] = (jour + dt.timedelta(days=delai)).isoformat()
    return en_mesure


def normaliser(url: str) -> str:
    return url.split("#")[0].split("?")[0].rstrip("/").lower()


# ─── Le classement ────────────────────────────────────────────────

def classer(lignes: list[dict], lexique: list, marque: list[re.Pattern], jours: int,
            demande: dict[str, tuple[float, str]] | None = None, en_mesure: dict[str, str] | None = None,
            impressions_min: int = 30, gsc: bool = True) -> dict:
    """`gsc=False` : aucune donnée Search Console. Une requête absente des
    données ne veut alors pas dire que le site en est absent."""
    en_mesure = en_mesure or {}
    mensuel = 30 / max(jours, 1)
    par_requete: dict[str, dict] = {}
    for l in lignes:
        r = par_requete.setdefault(l["requete"].lower(), {"requete": l["requete"], "clics": 0.0,
                                                          "impressions": 0.0, "pos_x_impr": 0.0, "pages": {}})
        r["clics"] += l["clics"]
        r["impressions"] += l["impressions"]
        r["pos_x_impr"] += l["position"] * l["impressions"]
        if l["page"]:
            r["pages"][l["page"]] = r["pages"].get(l["page"], 0.0) + l["impressions"]

    opportunites, marque_total, themes = [], {"clics": 0.0, "impressions": 0.0}, defaultdict(
        lambda: {"requetes": 0, "clics": 0.0, "impressions": 0.0, "meilleure_position": None, "pages": set()})
    for cle, r in par_requete.items():
        if any(m.search(r["requete"]) for m in marque):
            marque_total["clics"] += r["clics"]
            marque_total["impressions"] += r["impressions"]
            continue
        impr = r["impressions"]
        position = r["pos_x_impr"] / impr if impr else 0.0
        ctr = r["clics"] / impr if impr else 0.0
        theme, valeur = theme_de(r["requete"], lexique)
        t = themes[theme]
        t["requetes"] += 1
        t["clics"] += r["clics"]
        t["impressions"] += impr
        t["pages"].update(r["pages"])
        if position and (t["meilleure_position"] is None or position < t["meilleure_position"]):
            t["meilleure_position"] = round(position, 1)
        if impr < impressions_min:
            continue

        pages = sorted(r["pages"].items(), key=lambda x: -x[1])
        page = pages[0][0] if pages else ""
        concurrentes = [p for p, i in pages if i >= 0.2 * impr]
        if len(concurrentes) >= 2 and position <= 20:
            action, cible = "cannibalisation", max(1.0, position - 2)
        elif position <= 3.5:
            if ctr >= 0.6 * ctr_attendu(position):
                continue                                  # déjà au niveau attendu
            action, cible = "ctr", position
        elif position <= 10:
            action, cible = "page-1", max(1.0, position - 3)
        elif position <= 20:
            action, cible = "page-2", 7.0
        else:
            action, cible = "loin", 10.0
        # Pour un title, on vise 80 % du CTR attendu à la même position, pas plus.
        vise = 0.8 * ctr_attendu(position) if action == "ctr" else ctr_attendu(cible)
        gain = max(0.0, impr * mensuel * (vise - ctr))
        libelle, facilite, type_journal = ACTIONS[action]
        bloque = en_mesure.get(normaliser(page))
        opportunites.append({
            "requete": r["requete"], "page": page, "theme": theme, "valeur": valeur,
            "impressions_mois": round(impr * mensuel), "clics_mois": round(r["clics"] * mensuel, 1),
            "position": round(position, 1), "ctr_pct": round(ctr * 100, 2),
            "action": action, "a_faire": libelle, "type_journal": type_journal,
            "pages_concurrentes": concurrentes if action == "cannibalisation" else [],
            "gain_clics_mois": round(gain, 1),
            "score": 0.0 if bloque else round(gain * valeur * facilite, 1),
            "en_mesure_jusqu_au": bloque or "",
        })

    connues = set(par_requete)
    for requete, (volume, page) in (demande or {}).items():
        if any(m.search(requete) for m in marque):
            continue
        theme, valeur = theme_de(requete, lexique)
        if page:
            themes[theme]["pages"].add(page)        # la couverture compte la page, même sans volume
        if requete in connues or volume <= 0:
            continue
        gain = volume * ctr_attendu(8)
        action = ("invisible" if gsc else "a-verifier") if page else "a-creer"
        libelle, facilite, type_journal = ACTIONS[action]
        bloque = en_mesure.get(normaliser(page)) if page else ""
        opportunites.append({
            "requete": requete, "page": page, "theme": theme, "valeur": valeur,
            "impressions_mois": 0, "clics_mois": 0, "position": None, "ctr_pct": 0,
            "action": action, "a_faire": libelle, "type_journal": type_journal, "pages_concurrentes": [],
            "volume_mois": volume, "gain_clics_mois": round(gain, 1),
            "score": 0.0 if bloque else round(gain * valeur * facilite, 1), "en_mesure_jusqu_au": bloque or "",
        })

    opportunites.sort(key=lambda o: (-o["score"], -o["gain_clics_mois"]))

    par_page: dict[str, dict] = {}
    for o in opportunites:
        if not o["page"] or o["en_mesure_jusqu_au"]:
            continue
        p = par_page.setdefault(o["page"], {"page": o["page"], "score": 0.0, "gain_clics_mois": 0.0,
                                            "requetes": [], "actions": defaultdict(float)})
        p["score"] += o["score"]
        p["gain_clics_mois"] += o["gain_clics_mois"]
        p["requetes"].append(o["requete"])
        p["actions"][o["action"]] += o["score"]
    pages = sorted(par_page.values(), key=lambda p: -p["score"])
    for p in pages:
        p["action_principale"] = max(p["actions"], key=p["actions"].get)
        p["actions"] = dict(p["actions"])
        p["score"] = round(p["score"], 1)
        p["gain_clics_mois"] = round(p["gain_clics_mois"], 1)

    lexique_themes = {t for t, _, _ in lexique}
    couverture = [{"theme": t, **{k: (round(v, 1) if isinstance(v, float) else len(v) if isinstance(v, set) else v)
                                  for k, v in d.items()}}
                  for t, d in themes.items()]
    for t in sorted(lexique_themes - set(themes)):
        couverture.append({"theme": t, "requetes": 0, "clics": 0, "impressions": 0, "meilleure_position": None,
                           "pages": 0})
    couverture.sort(key=lambda c: (-c["impressions"], -c["pages"]))

    return {"gsc": gsc, "opportunites": opportunites, "pages": pages, "couverture": couverture,
            "marque": {k: round(v * mensuel) for k, v in marque_total.items()},
            "en_mesure": sorted(set(o["page"] for o in opportunites if o["en_mesure_jusqu_au"]))}


# ─── Sortie ───────────────────────────────────────────────────────

def rapport_markdown(res: dict, nom: str, jours: int, source: str, top: int, lexique_absent: bool) -> str:
    l = [f"# Opportunités SEO — {nom}", "",
         f"{dt.date.today():%d/%m/%Y} · {source} · {jours} jours, ramenés au mois", ""]
    if lexique_absent:
        l += ["> ⚠️ Aucun lexique (`memoire/lexique.csv`) : tous les thèmes ont la même valeur. "
              "Le classement suit le trafic, pas le chiffre d'affaires.", ""]
    l += ["## Les actions, dans l'ordre", "",
          "| # | Requête | Page | Pos. | Impr./mois | Thème (valeur) | Action | Gain estimé (clics/mois) |",
          "|---|---|---|---|---|---|---|---|"]
    for i, o in enumerate([o for o in res["opportunites"] if o["score"] > 0][:top], 1):
        page = o["page"].split("://", 1)[-1] if o["page"] else "—"
        pos = o["position"] if o["position"] is not None else ("absent" if res["gsc"] else "?")
        impr = o["impressions_mois"] or f"vol. {o.get('volume_mois', 0):.0f}"
        l.append(f"| {i} | {o['requete']} | {page} | {pos} | {impr} | {o['theme']} ({o['valeur']}) "
                 f"| {o['a_faire']} | {o['gain_clics_mois']} |")
    l += ["", "## Les pages à travailler", "",
          "| Page | Score | Gain estimé | Action principale | Requêtes |", "|---|---|---|---|---|"]
    for p in res["pages"][:15]:
        l.append(f"| {p['page'].split('://', 1)[-1]} | {p['score']} | {p['gain_clics_mois']} "
                 f"| {ACTIONS[p['action_principale']][0]} | {', '.join(p['requetes'][:4])} |")
    l += ["", "## Couverture par thème", "",
          "| Thème | Pages | Requêtes | Impressions | Clics | Meilleure position |", "|---|---|---|---|---|---|"]
    for c in res["couverture"]:
        if c["meilleure_position"] is not None:
            pos = c["meilleure_position"]
        elif not c["pages"]:
            pos = "**aucune page**"
        else:
            pos = "invisible" if res["gsc"] else "?"
        l.append(f"| {c['theme']} | {c['pages']} | {c['requetes']} | {c['impressions']:.0f} | {c['clics']:.0f} | {pos} |")
    l += ["", f"Marque : {res['marque']['clics']} clics et {res['marque']['impressions']} impressions par mois "
              "(hors classement)."]
    if res["en_mesure"]:
        l += ["", "Pages en cours de mesure, volontairement exclues : " + ", ".join(res["en_mesure"])]
    l += ["", "Les gains sont des ordres de grandeur pour comparer les actions entre elles. "
              "Le gain réel se lit à J+28 dans le journal de mesure.", ""]
    return "\n".join(l)


def main() -> int:
    charger_env()
    ap = argparse.ArgumentParser(description="Classement des opportunités SEO du projet")
    ap.add_argument("--jours", type=int, default=90)
    ap.add_argument("--csv", help="export Search Console (requête, page, clics, impressions, position)")
    ap.add_argument("--site", help="propriété Search Console (défaut : config du projet)")
    ap.add_argument("--demande", help="CSV requete,volume : la demande où le site n'apparaît pas encore")
    ap.add_argument("--lexique", default="memoire/lexique.csv")
    ap.add_argument("--impressions-min", type=int, default=30, help="sur la période")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--ecrire", action="store_true", help="écrit rapports/opportunites-AAAA-MM-JJ.md")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    racine = racine_projet()
    chemin_lexique = Path(a.lexique) if Path(a.lexique).is_absolute() else racine / a.lexique
    lexique = lire_lexique(chemin_lexique)
    if a.csv:
        lignes, source = lire_csv_gsc(Path(a.csv)), f"export {Path(a.csv).name}"
    else:
        try:
            lignes, source = lire_gsc(a.jours, a.site), "Search Console"
        except Exception as exc:  # ErreurGSC, réseau : on dit quoi faire plutôt que planter
            if not a.demande:
                print(f"✗ Search Console indisponible : {exc}\n  → exportez Performances (requêtes × pages) "
                      "et relancez avec --csv", file=sys.stderr)
                return 1
            # Site jeune ou accès pas encore donné : la demande seule classe déjà les pages à créer.
            print(f"  ! Search Console indisponible ({str(exc)[:80]}) : classement sur la demande seule",
                  file=sys.stderr)
            lignes, source = [], "demande seule (Search Console indisponible)"
    demande = lire_demande(Path(a.demande)) if a.demande else None
    delai = int(lire_valeur("mesure.delai_jours", "28") or 28)
    res = classer(lignes, lexique, motifs_marque(), a.jours, demande, pages_en_mesure(delai), a.impressions_min,
                  gsc=bool(lignes) or bool(a.csv))

    if a.json:
        print(json.dumps({"source": source, "jours": a.jours, **res}, ensure_ascii=False, indent=1))
        return 0
    texte = rapport_markdown(res, lire_valeur("projet.nom", "le projet"), a.jours, source, a.top, not lexique)
    if a.ecrire:
        cible = racine / "rapports" / f"opportunites-{dt.date.today().isoformat()}.md"
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(texte, encoding="utf-8")
        print(f"  ✓ {cible.relative_to(racine)}")
    else:
        print(texte)
    return 0


if __name__ == "__main__":
    sys.exit(main())
