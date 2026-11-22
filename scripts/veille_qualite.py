#!/usr/bin/env python3
"""Historique de la veille qualité des pages publiées (skill seo-veille-qualite).

    veille_qualite.py ajouter --url U --motcle "m" --a 16 --b 12 --c 10 --d 8 --e 17 \
        [--position 11.4] [--impressions 820] [--note "..."] [--date AAAA-MM-JJ]
    veille_qualite.py classement [--json]   # dernière note par page, les plus faibles d'abord
    veille_qualite.py correler [--seuil 80] [--json]
        # les pages bien notées gagnent-elles plus souvent à J+28 ?

Les notes vivent dans donnees/qualite.csv (une ligne par page et par relevé).
Chaque bloc de la grille (A à E) vaut 20 points : références/grille-veille.md.
Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import racine_projet  # noqa: E402

BLOCS = ("a", "b", "c", "d", "e")
NOMS_BLOCS = {"a": "intention et SERP", "b": "valeur et gap sémantique", "c": "concurrence",
              "d": "GEO", "e": "on-page et confiance"}
COLONNES = ["date", "url", "motcle", *BLOCS, "total", "position", "impressions", "note"]


def chemin_historique() -> Path:
    return racine_projet() / "donnees" / "qualite.csv"


def lire() -> list[dict]:
    chemin = chemin_historique()
    if not chemin.is_file():
        return []
    with open(chemin, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def normaliser(url: str) -> str:
    return url.strip().rstrip("/").lower()


def cmd_ajouter(a) -> int:
    notes = {b: getattr(a, b) for b in BLOCS}
    for b, v in notes.items():
        if not 0 <= v <= 20:
            print(f"✗ bloc {b.upper()} : {v} hors de 0-20", file=sys.stderr)
            return 2
    ligne = {"date": a.date or dt.date.today().isoformat(), "url": a.url.strip(), "motcle": a.motcle,
             **{b: str(v) for b, v in notes.items()}, "total": str(sum(notes.values())),
             "position": "" if a.position is None else str(a.position),
             "impressions": "" if a.impressions is None else str(a.impressions), "note": a.note or ""}
    chemin = chemin_historique()
    chemin.parent.mkdir(parents=True, exist_ok=True)
    neuf = not chemin.is_file()
    with open(chemin, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES)
        if neuf:
            w.writeheader()
        w.writerow(ligne)
    print(f"✓ {ligne['url']} : {ligne['total']}/100 ({chemin})")
    return 0


def classement(lignes: list[dict]) -> list[dict]:
    par_page: dict[str, list[dict]] = {}
    for l in lignes:
        par_page.setdefault(normaliser(l["url"]), []).append(l)
    sortie = []
    for releves in par_page.values():
        releves.sort(key=lambda l: l["date"])
        dernier = releves[-1]
        precedent = releves[-2] if len(releves) > 1 else None
        notes = {b: int(dernier[b]) for b in BLOCS}
        faible = min(BLOCS, key=lambda b: notes[b])
        sortie.append({
            "url": dernier["url"], "motcle": dernier["motcle"], "date": dernier["date"],
            "total": int(dernier["total"]),
            "evolution": None if not precedent else int(dernier["total"]) - int(precedent["total"]),
            "bloc_faible": NOMS_BLOCS[faible], "note_bloc_faible": notes[faible],
            "position": dernier.get("position") or None,
        })
    # Les plus faibles d'abord ; à note égale, la note la plus ancienne d'abord.
    sortie.sort(key=lambda e: (e["total"], e["date"]))
    return sortie


def cmd_classement(a) -> int:
    rang = classement(lire())
    if a.json:
        print(json.dumps(rang, ensure_ascii=False, indent=1))
        return 0
    if not rang:
        print("Aucune page notée (donnees/qualite.csv absent ou vide).")
        return 0
    print(f"\n  {'Score':>5}  {'Évol.':>5}  Page — bloc le plus faible")
    for e in rang:
        evol = "  —" if e["evolution"] is None else f"{e['evolution']:+d}"
        print(f"  {e['total']:>5}  {evol:>5}  {e['url']} — {e['bloc_faible']} "
              f"({e['note_bloc_faible']}/20, noté le {e['date']})")
    return 0


def lire_journal() -> list[dict]:
    chemin = racine_projet() / "journal" / "modifications.csv"
    if not chemin.is_file():
        return []
    with open(chemin, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def correler(qualite: list[dict], journal: list[dict], seuil: int) -> dict:
    """Taux de gain à J+28 des modifications, selon la note qualité de la page à ce moment-là."""
    notes_par_page: dict[str, list[tuple[str, int]]] = {}
    for l in qualite:
        notes_par_page.setdefault(normaliser(l["url"]), []).append((l["date"], int(l["total"])))
    groupes = {"haute": {"gain": 0, "neutre": 0, "perte": 0},
               "basse": {"gain": 0, "neutre": 0, "perte": 0}}
    for m in journal:
        verdict = m.get("verdict")
        if verdict not in ("gain", "neutre", "perte"):
            continue
        notes = sorted(notes_par_page.get(normaliser(m.get("url", "")), []))
        anterieures = [n for d, n in notes if d <= (m.get("date") or "")]
        if not anterieures:
            continue
        groupe = "haute" if anterieures[-1] >= seuil else "basse"
        groupes[groupe][verdict] += 1

    def taux(g):
        total = sum(g.values())
        return None if total == 0 else round(100 * g["gain"] / total)

    resultat = {"seuil": seuil, "haute": groupes["haute"], "basse": groupes["basse"],
                "taux_gain_haute": taux(groupes["haute"]), "taux_gain_basse": taux(groupes["basse"])}
    th, tb = resultat["taux_gain_haute"], resultat["taux_gain_basse"]
    jugeables = sum(groupes["haute"].values()) >= 3 and sum(groupes["basse"].values()) >= 3
    if not jugeables:
        resultat["lecture"] = "pas assez de mesures (au moins 3 par groupe) pour juger la grille"
    elif th > tb:
        resultat["lecture"] = "la grille prédit : les pages bien notées gagnent plus souvent"
    else:
        resultat["lecture"] = ("la grille ne prédit pas les gains : un bloc est mal pondéré, "
                               "à signaler dans le rapport")
    return resultat


def cmd_correler(a) -> int:
    r = correler(lire(), lire_journal(), a.seuil)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0
    def ligne(nom, g, t):
        return (f"  {nom:<16} gain {g['gain']} · neutre {g['neutre']} · perte {g['perte']}"
                f" → {'—' if t is None else str(t) + ' % de gains'}")
    print(f"\n  Seuil : {r['seuil']}/100")
    print(ligne(f"note ≥ {r['seuil']}", r["haute"], r["taux_gain_haute"]))
    print(ligne(f"note < {r['seuil']}", r["basse"], r["taux_gain_basse"]))
    print(f"\n  {r['lecture']}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sp = p.add_subparsers(dest="cmd", required=True)
    aj = sp.add_parser("ajouter", help="enregistrer la note d'une page")
    aj.add_argument("--url", required=True)
    aj.add_argument("--motcle", required=True)
    for b in BLOCS:
        aj.add_argument(f"--{b}", type=int, required=True, help=f"bloc {b.upper()} ({NOMS_BLOCS[b]}), sur 20")
    aj.add_argument("--position", type=float)
    aj.add_argument("--impressions", type=int)
    aj.add_argument("--note")
    aj.add_argument("--date", help="AAAA-MM-JJ (défaut : aujourd'hui)")
    cl = sp.add_parser("classement", help="dernière note par page, les plus faibles d'abord")
    cl.add_argument("--json", action="store_true")
    co = sp.add_parser("correler", help="la note prédit-elle les gains à J+28 ?")
    co.add_argument("--seuil", type=int, default=80)
    co.add_argument("--json", action="store_true")
    a = p.parse_args()
    return {"ajouter": cmd_ajouter, "classement": cmd_classement, "correler": cmd_correler}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
