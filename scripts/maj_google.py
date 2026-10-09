#!/usr/bin/env python3
"""Mises à jour du classement Google : dates officielles de début et de fin, sans se fier à la mémoire d'un modèle.

    python3 maj_google.py                          # les 10 dernières
    python3 maj_google.py --depuis 2025-06 --type core
    python3 maj_google.py periode 2026-09-20 2026-10-05   # ce qui recouvre une chute de trafic
    python3 maj_google.py en-cours                 # code 1 si un déploiement est en cours
    python3 maj_google.py --json

Source : le tableau de bord Google Search Status, service « Ranking »
(https://status.search.google.com/incidents.json), lu à chaque appel et
gardé un jour en cache dans .seo-decupler/cache/. Le flux ne remonte qu'à
un an : config/mises-a-jour-google.json garde l'historique plus ancien,
avec la page Google qui le source. Les rumeurs (mises à jour « détectées »
par des outils tiers, systèmes supposés) vont dans « non_verifie » de ce
fichier et ne servent jamais à un diagnostic.

`periode` répond à la question du diagnostic de chute : une mise à jour
recouvre-t-elle la période, déploiement compris, plus 7 jours après sa fin
(le temps que les positions se stabilisent) ? Pendant un déploiement on
ne modifie rien et on ne conclut rien (seo-veille, seo-traffic-drop).
Sans dépendance (Python 3.9+).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import dossier_etat  # noqa: E402

FLUX = "https://status.search.google.com/incidents.json"
HISTORIQUE = Path(__file__).resolve().parent.parent / "config" / "mises-a-jour-google.json"
MARGE_JOURS = 7
CACHE_SECONDES = 86_400
TYPES = ("core", "spam", "discover", "autre")


def type_de(nom: str) -> str:
    n = nom.lower()
    if "discover" in n:
        return "discover"
    if "core update" in n:
        return "core"
    if "spam" in n:
        return "spam"
    return "autre"


def depuis_flux(incidents: list) -> list[dict]:
    """Les incidents du service Ranking, au format de l'historique."""
    res = []
    for i in incidents:
        if i.get("service_name") != "Ranking":
            continue
        nom = i.get("external_desc", "").strip()
        fin = (i.get("end") or "")[:10] or None
        res.append({"debut": i["begin"][:10], "fin": fin, "type": type_de(nom), "nom": nom,
                    "source": f"https://status.search.google.com/{i.get('uri', '')}".rstrip("/"),
                    "notes": ((i.get("most_recent_update") or {}).get("text") or "").strip(),
                    "en_cours": fin is None})
    return res


def lire_flux(cache: Path | None = None, delai: int = 20) -> tuple[list, str]:
    """(incidents, origine) : le flux, son cache s'il a moins d'un jour, sinon le cache périmé."""
    cache = cache or dossier_etat("cache") / "google-status.json"
    if cache.is_file() and time.time() - cache.stat().st_mtime < CACHE_SECONDES:
        return json.loads(cache.read_text(encoding="utf-8")), "cache du jour"
    try:
        req = urllib.request.Request(FLUX, headers={"User-Agent": "decupler-seo maj_google"})
        with urllib.request.urlopen(req, timeout=delai) as r:
            brut = r.read().decode()
        incidents = json.loads(brut)
        try:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(brut, encoding="utf-8")
        except OSError:
            pass
        return incidents, "tableau de bord Google"
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        if cache.is_file():
            return json.loads(cache.read_text(encoding="utf-8")), f"cache périmé (flux injoignable : {e})"
        return [], f"historique seul (flux injoignable : {e})"


def toutes(historique: dict, incidents: list) -> list[dict]:
    """Historique + flux, sans doublon (le flux gagne : il porte la fin réelle), du plus récent au plus ancien."""
    par_cle = {}
    for m in historique.get("mises_a_jour", []):
        par_cle[(m["nom"].lower(), m["debut"][:7])] = {**m, "en_cours": False}
    for m in depuis_flux(incidents):
        par_cle[(m["nom"].lower(), m["debut"][:7])] = m
    return sorted(par_cle.values(), key=lambda m: m["debut"], reverse=True)


def _date(s: str) -> dt.date:
    return dt.date.fromisoformat(s[:10])


def recouvre(m: dict, debut: dt.date, fin: dt.date, aujourdhui: dt.date) -> bool:
    """La mise à jour, déploiement plus MARGE_JOURS, touche-t-elle [debut, fin] ?"""
    m_fin = _date(m["fin"]) if m.get("fin") else aujourdhui
    return _date(m["debut"]) <= fin and m_fin + dt.timedelta(days=MARGE_JOURS) >= debut


def filtrer(maj: list, depuis: str | None, types: list[str] | None) -> list:
    if depuis:
        maj = [m for m in maj if m["debut"] >= depuis]
    if types:
        maj = [m for m in maj if m["type"] in types]
    return maj


def duree(m: dict, aujourdhui: dt.date) -> str:
    fin = _date(m["fin"]) if m.get("fin") else None
    if m.get("en_cours"):
        return f"en cours depuis {(aujourdhui - _date(m['debut'])).days} j"
    if fin:
        return f"{(fin - _date(m['debut'])).days} j"
    return "fin non sourcée"


def ligne(m: dict, aujourdhui: dt.date) -> str:
    fin = m.get("fin") or ("…" if m.get("en_cours") else "?")
    return f"  {m['debut']} → {fin:<10}  {m['type']:<8} {m['nom']}  ({duree(m, aujourdhui)})"


def main() -> int:
    ap = argparse.ArgumentParser(description="Mises à jour du classement Google, dates officielles")
    ap.add_argument("commande", nargs="?", default="liste", choices=["liste", "periode", "en-cours", "rumeurs"])
    ap.add_argument("dates", nargs="*", help="periode : DEBUT [FIN] au format AAAA-MM-JJ")
    ap.add_argument("--depuis", help="AAAA ou AAAA-MM ou AAAA-MM-JJ")
    ap.add_argument("--type", action="append", choices=TYPES, help="core, spam, discover, autre (répétable)")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--hors-ligne", action="store_true", help="ne pas lire le flux Google")
    a = ap.parse_args()

    historique = json.loads(HISTORIQUE.read_text(encoding="utf-8"))
    if a.commande == "rumeurs":
        nv = historique.get("non_verifie", [])
        if a.json:
            print(json.dumps(nv, ensure_ascii=False, indent=2))
        else:
            for r in nv:
                print(f"  {r['date']}  {r['affirmation']}\n      → {r['statut']}")
        return 0
    incidents, origine = ([], "historique seul (--hors-ligne)") if a.hors_ligne else lire_flux()
    maj = filtrer(toutes(historique, incidents), a.depuis, a.type)
    aujourdhui = dt.date.today()

    if a.commande == "en-cours":
        cours = [m for m in maj if m.get("en_cours")]
        if a.json:
            print(json.dumps({"origine": origine, "en_cours": cours}, ensure_ascii=False, indent=2))
        elif cours:
            print("Déploiement en cours — ne rien modifier, ne rien conclure :")
            print("\n".join(ligne(m, aujourdhui) for m in cours))
        else:
            print(f"Aucun déploiement en cours ({origine}).")
        return 1 if cours else 0

    if a.commande == "periode":
        if not a.dates:
            ap.error("periode attend DEBUT [FIN]")
        debut = _date(a.dates[0])
        fin = _date(a.dates[1]) if len(a.dates) > 1 else aujourdhui
        touchees = [m for m in maj if recouvre(m, debut, fin, aujourdhui)]
        if a.json:
            print(json.dumps({"origine": origine, "debut": str(debut), "fin": str(fin),
                              "marge_jours": MARGE_JOURS, "mises_a_jour": touchees}, ensure_ascii=False, indent=2))
            return 0
        print(f"Du {debut} au {fin} ({origine}, marge de {MARGE_JOURS} j après chaque fin) :")
        if not touchees:
            print("  aucune mise à jour du classement : la cause est à chercher sur le site ou la demande.")
        for m in touchees:
            print(ligne(m, aujourdhui))
            if m.get("en_cours"):
                print("      → déploiement en cours : attendre la fin + 7 jours avant de comparer.")
        return 0

    if a.json:
        print(json.dumps({"origine": origine, "mises_a_jour": maj[:a.n]}, ensure_ascii=False, indent=2))
        return 0
    print(f"Mises à jour du classement Google ({origine}) :")
    print("\n".join(ligne(m, aujourdhui) for m in maj[:a.n]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
