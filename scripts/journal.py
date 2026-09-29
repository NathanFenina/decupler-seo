#!/usr/bin/env python3
"""Journal des modifications SEO et mesure de leur effet à J+28.

    python3 journal.py ajouter --url https://exemple.com/page --type title \\
        --avant "Ancien titre" --apres "Nouveau titre" --requete "mot clé" \\
        --clics 41 --impressions 3200 --position 11.4 --ctr 1.3
    python3 journal.py echeances
    python3 journal.py mesurer --id 7 --clics 96 --impressions 3350 --position 7.2 --ctr 2.9 --temoin 4
    python3 journal.py a-annuler
    python3 journal.py bilan

Toute modification publiée par le dispositif passe par ici AVANT d'être
considérée comme faite. Sans situation de départ enregistrée, on ne saura
jamais si elle a aidé ou nui — et une publication automatique qu'on ne peut
ni évaluer ni annuler n'est pas défendable.

Les chiffres (clics, impressions, position, CTR) sont ceux de Search Console
sur les 28 jours précédant la modification, puis sur les 28 jours précédant
la mesure. Mêmes durées de part et d'autre, sinon la comparaison est fausse.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import fichier_config, racine_projet  # noqa: E402

COLONNES = [
    "id", "date", "url", "requete", "type", "niveau", "avant", "apres",
    "clics_avant", "impressions_avant", "position_avant", "ctr_avant",
    "date_mesure", "clics_apres", "impressions_apres", "position_apres", "ctr_apres",
    "variation_temoin_pct", "verdict", "note",
]
TYPES = ["title", "meta", "faq", "schema", "maillage", "contenu", "reecriture-section", "page-neuve", "technique"]
NIVEAUX = {"title": "automatique", "meta": "automatique", "faq": "automatique",
           "schema": "automatique", "maillage": "automatique", "technique": "automatique",
           "contenu": "validation", "reecriture-section": "validation", "page-neuve": "validation"}

# En dessous de ce volume de clics, une variation en pourcentage ne veut rien
# dire (passer de 2 à 4 clics fait +100 %) : on juge alors sur la position.
CLICS_MIN_POUR_JUGER_EN_CLICS = 20


def reglages() -> dict:
    defauts = {"delai_jours": 28, "impressions_min_pour_juger": 100,
               "seuil_gain_pct": 10.0, "seuil_perte_pct": -15.0}
    config = fichier_config()
    if not config:
        return defauts
    for ligne in config.read_text(encoding="utf-8").splitlines():
        nue = ligne.split("#", 1)[0].strip()
        cle, _, valeur = nue.partition(":")
        if cle.strip() in defauts and valeur.strip():
            try:
                defauts[cle.strip()] = float(valeur)
            except ValueError:
                pass
    return defauts


def chemin_journal() -> Path:
    return racine_projet() / "journal" / "modifications.csv"


def lire() -> list[dict]:
    chemin = chemin_journal()
    if not chemin.is_file():
        return []
    with open(chemin, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ecrire(lignes: list[dict]) -> None:
    chemin = chemin_journal()
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES)
        w.writeheader()
        for l in lignes:
            w.writerow({c: l.get(c, "") for c in COLONNES})


def nombre(v) -> float | None:
    try:
        return float(str(v).replace(",", ".").replace("%", "").strip())
    except (TypeError, ValueError):
        return None


def juger(l: dict, r: dict) -> tuple[str, str]:
    """Renvoie (verdict, explication). Verdicts : gain, neutre, perte, insuffisant."""
    c0, c1 = nombre(l["clics_avant"]), nombre(l["clics_apres"])
    i0 = nombre(l["impressions_avant"])
    p0, p1 = nombre(l["position_avant"]), nombre(l["position_apres"])
    temoin = nombre(l.get("variation_temoin_pct")) or 0.0

    if i0 is None or c0 is None or c1 is None:
        return "insuffisant", "situation de départ ou d'arrivée manquante"
    if i0 < r["impressions_min_pour_juger"]:
        return "insuffisant", f"{int(i0)} impressions au départ, sous le seuil de {int(r['impressions_min_pour_juger'])}"

    if c0 >= CLICS_MIN_POUR_JUGER_EN_CLICS:
        brut = (c1 - c0) / c0 * 100
        net = brut - temoin
        detail = f"clics {int(c0)} → {int(c1)} ({brut:+.0f} %, témoin {temoin:+.0f} %, net {net:+.0f} %)"
        if net >= r["seuil_gain_pct"] and c1 - c0 >= 3:
            return "gain", detail
        if net <= r["seuil_perte_pct"] and c0 - c1 >= 3:
            return "perte", detail
        return "neutre", detail

    # Peu de clics : la position est le seul signal exploitable.
    if p0 is None or p1 is None:
        return "insuffisant", f"seulement {int(c0)} clics au départ et position absente"
    ecart = p0 - p1  # positif = la page est montée
    detail = f"position {p0:.1f} → {p1:.1f} ({ecart:+.1f}), {int(c0)} → {int(c1)} clics"
    if ecart >= 2:
        return "gain", detail
    if ecart <= -3:
        return "perte", detail
    return "neutre", detail


def cmd_ajouter(a) -> int:
    lignes = lire()
    r = reglages()
    prochain = max((int(l["id"]) for l in lignes if l["id"].isdigit()), default=0) + 1
    aujourd_hui = dt.date.today()
    ligne = {
        "id": str(prochain), "date": aujourd_hui.isoformat(), "url": a.url,
        "requete": a.requete or "", "type": a.type, "niveau": NIVEAUX.get(a.type, ""),
        "avant": a.avant or "", "apres": a.apres or "",
        "clics_avant": a.clics if a.clics is not None else "",
        "impressions_avant": a.impressions if a.impressions is not None else "",
        "position_avant": a.position if a.position is not None else "",
        "ctr_avant": a.ctr if a.ctr is not None else "",
        "date_mesure": (aujourd_hui + dt.timedelta(days=int(r["delai_jours"]))).isoformat(),
        "note": a.note or "",
    }
    lignes.append(ligne)
    ecrire(lignes)
    print(f"  ✓ Modification #{prochain} journalisée ({a.type} sur {a.url}), mesure le {ligne['date_mesure']}")
    if a.clics is None or a.impressions is None:
        print("  ! Situation de départ incomplète : cette modification ne pourra pas être jugée.")
        print("    Relevez clics et impressions des 28 derniers jours dans Search Console.")
    return 0


def cmd_echeances(a) -> int:
    aujourd_hui = dt.date.today().isoformat()
    dues = [l for l in lire() if not l["verdict"] and l["date_mesure"] and l["date_mesure"] <= aujourd_hui]
    if a.json:
        print(json.dumps(dues, ensure_ascii=False, indent=1))
        return 0
    if not dues:
        print("  Aucune modification à mesurer aujourd'hui.")
        return 0
    print(f"  {len(dues)} modification(s) à mesurer :\n")
    for l in dues:
        print(f"  #{l['id']:<4} {l['type']:<18} {l['url']}")
        print(f"        requête : {l['requete'] or '—'} · départ : {l['clics_avant'] or '?'} clics, "
              f"position {l['position_avant'] or '?'} · journalisée le {l['date']}")
    print("\n  Relevez les 28 derniers jours dans Search Console pour chaque URL, puis :")
    print("  journal.py mesurer --id N --clics … --impressions … --position … --ctr … --temoin …")
    print("  --temoin = variation des clics (en %) des pages NON modifiées du site sur la même")
    print("  période. Elle neutralise la saisonnalité et les mises à jour Google.")
    return 0


def cmd_mesurer(a) -> int:
    lignes = lire()
    cible = next((l for l in lignes if l["id"] == str(a.id)), None)
    if not cible:
        print(f"  ✗ Modification #{a.id} introuvable.")
        return 1
    cible.update({
        "clics_apres": a.clics, "impressions_apres": a.impressions,
        "position_apres": a.position if a.position is not None else "",
        "ctr_apres": a.ctr if a.ctr is not None else "",
        "variation_temoin_pct": a.temoin if a.temoin is not None else "",
    })
    verdict, detail = juger(cible, reglages())
    cible["verdict"] = verdict
    cible["note"] = (cible.get("note", "") + f" | mesuré le {dt.date.today()} : {detail}").strip(" |")
    ecrire(lignes)
    icone = {"gain": "🟢", "neutre": "⚪", "perte": "🔴", "insuffisant": "·"}[verdict]
    print(f"  {icone} #{a.id} {cible['type']} — {verdict} : {detail}")
    if verdict == "perte":
        print(f"     Retour arrière proposé : remettre « {cible['avant'][:80]} »")
    return 0


def cmd_a_annuler(a) -> int:
    pertes = [l for l in lire() if l["verdict"] == "perte"]
    if not pertes:
        print("  Aucune modification à annuler.")
        return 0
    print(f"  {len(pertes)} modification(s) ont fait baisser leur page :\n")
    for l in pertes:
        print(f"  #{l['id']} {l['type']} — {l['url']}")
        print(f"     remettre : {l['avant'][:100]}")
        print(f"     mesure   : {l['note'].split('|')[-1].strip()}\n")
    print("  Un retour arrière est lui-même une modification : journalisez-le.")
    return 0


def cmd_bilan(a) -> int:
    mesurees = [l for l in lire() if l["verdict"]]
    par_type: dict[str, Counter] = defaultdict(Counter)
    for l in mesurees:
        par_type[l["type"]][l["verdict"]] += 1

    # Un apprentissage exige au moins 3 mesures jugeables du même type, et
    # une majorité nette. En dessous, c'est du bruit : on ne conclut pas.
    apprentissages = []
    for type_, c in par_type.items():
        jugeables = c["gain"] + c["neutre"] + c["perte"]
        if jugeables < 3:
            continue
        if c["gain"] / jugeables >= 0.6:
            apprentissages.append(("marche", type_, c, jugeables))
        elif c["perte"] / jugeables >= 0.4:
            apprentissages.append(("echoue", type_, c, jugeables))

    if a.json:
        print(json.dumps({"par_type": {t: dict(c) for t, c in par_type.items()},
                          "apprentissages": [{"sens": s, "type": t, "jugeables": j, **dict(c)}
                                             for s, t, c, j in apprentissages]},
                         ensure_ascii=False, indent=1))
        return 0

    if not mesurees:
        print("  Aucune modification mesurée pour l'instant.")
        return 0
    print(f"  {len(mesurees)} modification(s) mesurée(s)\n")
    print(f"  {'type':<20}{'gain':>6}{'neutre':>8}{'perte':>7}{'insuff.':>9}")
    for type_, c in sorted(par_type.items()):
        print(f"  {type_:<20}{c['gain']:>6}{c['neutre']:>8}{c['perte']:>7}{c['insuffisant']:>9}")
    if apprentissages:
        print("\n  À reporter dans memoire/apprentissages.md :")
        for sens, type_, c, j in apprentissages:
            libelle = "fonctionne" if sens == "marche" else "nuit souvent"
            print(f"   · « {type_} » {libelle} sur ce site ({c['gain']} gains, {c['perte']} pertes sur {j})")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Journal et mesure des modifications SEO")
    sp = p.add_subparsers(dest="commande", required=True)

    aj = sp.add_parser("ajouter")
    aj.add_argument("--url", required=True)
    aj.add_argument("--type", required=True, choices=TYPES)
    aj.add_argument("--requete")
    aj.add_argument("--avant")
    aj.add_argument("--apres")
    aj.add_argument("--clics", type=float)
    aj.add_argument("--impressions", type=float)
    aj.add_argument("--position", type=float)
    aj.add_argument("--ctr", type=float)
    aj.add_argument("--note")

    e = sp.add_parser("echeances")
    e.add_argument("--json", action="store_true")

    m = sp.add_parser("mesurer")
    m.add_argument("--id", required=True, type=int)
    m.add_argument("--clics", required=True, type=float)
    m.add_argument("--impressions", required=True, type=float)
    m.add_argument("--position", type=float)
    m.add_argument("--ctr", type=float)
    m.add_argument("--temoin", type=float, help="variation des clics des pages non modifiées, en %%")

    sp.add_parser("a-annuler")
    b = sp.add_parser("bilan")
    b.add_argument("--json", action="store_true")

    a = p.parse_args()
    return {"ajouter": cmd_ajouter, "echeances": cmd_echeances, "mesurer": cmd_mesurer,
            "a-annuler": cmd_a_annuler, "bilan": cmd_bilan}[a.commande](a)


if __name__ == "__main__":
    sys.exit(main())
