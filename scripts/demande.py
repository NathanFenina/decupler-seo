#!/usr/bin/env python3
"""La demande de recherche, par l'API DataForSEO — sans connecteur, donc aussi dans une routine.

    python3 demande.py volumes --mots "création entreprise, expert comptable lyon" --langue fr
    python3 demande.py idees --graines "création entreprise" --langue fr --max 100
    python3 demande.py idees --lexique --langue ar            # graines = thèmes du lexique du projet
    python3 demande.py serp --mot "expert comptable lyon" --langue fr

- `volumes` : volume mensuel, CPC et concurrence de mots-clés donnés.
- `idees`   : mots-clés liés à des graines, avec volume, difficulté et intention.
              Écrit donnees/demande-<langue>-<date>.csv (requete,volume,kd,intention,
              tendance_an_pct,page),
              directement utilisable par opportunites.py --demande.
- `serp`    : top 10 organique, questions « Autres questions posées », présence
              d'un AI Overview et recherches associées. C'est la matière du brief.

Le pays vient de projet.pays_cible (config) ou de --pays, la langue de --langue.
Identifiants : DATAFORSEO_LOGIN (ou DATAFORSEO_USERNAME) et DATAFORSEO_PASSWORD.
Chaque appel affiche son coût réel, renvoyé par l'API. Sans dépendance.
"""

from __future__ import annotations

import argparse
import base64
import csv
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import charger_env, lire_valeur, racine_projet  # noqa: E402

API = "https://api.dataforseo.com/v3"

# Codes pays ISO → nom de lieu DataForSEO. Les marchés courants ; --lieu pour les autres.
LIEUX = {"FR": "France", "BE": "Belgium", "CH": "Switzerland", "CA": "Canada", "LU": "Luxembourg",
         "MA": "Morocco", "TN": "Tunisia", "DZ": "Algeria", "SN": "Senegal", "CI": "Cote d'Ivoire",
         "SA": "Saudi Arabia", "AE": "United Arab Emirates", "QA": "Qatar", "KW": "Kuwait", "EG": "Egypt",
         "US": "United States", "GB": "United Kingdom", "DE": "Germany", "ES": "Spain", "IT": "Italy"}


class ErreurAPI(RuntimeError):
    pass


def identifiants() -> tuple[str, str]:
    login = os.environ.get("DATAFORSEO_LOGIN", "").strip() or os.environ.get("DATAFORSEO_USERNAME", "").strip()
    mdp = os.environ.get("DATAFORSEO_PASSWORD", "").strip()
    if not (login and mdp):
        raise ErreurAPI("identifiants absents : DATAFORSEO_LOGIN (ou DATAFORSEO_USERNAME) et DATAFORSEO_PASSWORD")
    return login, mdp


def appel(chemin: str, taches: list[dict]) -> tuple[list[dict], float]:
    """POST sur un point d'entrée « live » ; renvoie (résultats, coût en $)."""
    login, mdp = identifiants()
    jeton = base64.b64encode(f"{login}:{mdp}".encode()).decode()
    requete = urllib.request.Request(f"{API}/{chemin}", data=json.dumps(taches).encode(), method="POST",
                                     headers={"Authorization": f"Basic {jeton}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(requete, timeout=120) as rep:
            d = json.loads(rep.read())
    except urllib.error.HTTPError as exc:
        raise ErreurAPI(f"HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ErreurAPI(str(exc)[:120]) from None
    if d.get("status_code") != 20000:
        raise ErreurAPI(f"{d.get('status_code')} {d.get('status_message')}")
    resultats = []
    for t in d.get("tasks", []):
        if t.get("status_code") != 20000:
            raise ErreurAPI(f"tâche {t.get('status_code')} {t.get('status_message')}")
        resultats += t.get("result") or []
    return resultats, float(d.get("cost") or 0)


def lieu_et_langue(a) -> tuple[str, str]:
    pays = (a.pays or lire_valeur("projet.pays_cible") or "FR").upper()
    lieu = a.lieu or LIEUX.get(pays)
    if not lieu:
        raise SystemExit(f"✗ pays {pays} inconnu : passez --lieu \"Nom du pays en anglais\"")
    langue = (a.langue or "fr").lower()
    return lieu, langue


# ─── Commandes ────────────────────────────────────────────────────

def cmd_volumes(a) -> dict:
    lieu, langue = lieu_et_langue(a)
    mots = [m.strip() for m in (a.mots or "").split(",") if m.strip()]
    if a.fichier:
        with open(a.fichier, encoding="utf-8-sig") as f:
            mots += [l[0].strip() for l in csv.reader(f) if l and l[0].strip() and l[0].strip().lower() != "requete"]
    if not mots:
        raise SystemExit("✗ aucun mot-clé : --mots \"a, b\" ou --fichier liste.csv")
    res, cout = appel("keywords_data/google_ads/search_volume/live",
                      [{"keywords": mots[:1000], "location_name": lieu, "language_code": langue}])
    lignes = [{"requete": r.get("keyword"), "volume": r.get("search_volume") or 0, "cpc": r.get("cpc"),
               "concurrence": r.get("competition")} for r in res]
    lignes.sort(key=lambda x: -(x["volume"] or 0))
    return {"lieu": lieu, "langue": langue, "cout_usd": cout, "lignes": lignes}


def graines_du_lexique() -> list[str]:
    """Une graine lisible par thème : le premier motif sans syntaxe d'expression régulière."""
    chemin = racine_projet() / "memoire" / "lexique.csv"
    if not chemin.is_file():
        raise SystemExit("✗ memoire/lexique.csv absent : passez --graines")
    graines = {}
    with chemin.open(encoding="utf-8") as f:
        for l in csv.DictReader(f):
            motif = (l.get("motif") or "").split("|")[0]
            if not re.search(r"[\\\[\]()?*+^$]", motif) and l.get("theme") not in graines and motif.strip():
                graines[l["theme"]] = motif.strip()
    return list(graines.values())


def cmd_idees(a) -> dict:
    lieu, langue = lieu_et_langue(a)
    graines = graines_du_lexique() if a.lexique else [g.strip() for g in (a.graines or "").split(",") if g.strip()]
    if not graines:
        raise SystemExit("✗ aucune graine : --graines \"a, b\" ou --lexique")
    # « suggestions » garde la graine dans la requête (longue traîne fidèle au sujet) ;
    # « proches » élargit au voisinage sémantique. keyword_ideas, trop large, dérive
    # vers des sujets sans rapport : testé, écarté.
    chemin = {"suggestions": "dataforseo_labs/google/keyword_suggestions/live",
              "proches": "dataforseo_labs/google/related_keywords/live"}[a.mode]
    vues: dict[str, dict] = {}
    cout = 0.0
    for graine in graines[:20]:
        tache = {"keyword": graine, "location_name": lieu, "language_code": langue, "limit": a.max}
        if a.mode == "proches":
            tache["depth"] = 1
        res, c = appel(chemin, [tache])
        cout += c
        for r in res:
            for it in r.get("items") or []:
                it = it.get("keyword_data") or it          # related_keywords imbrique la donnée
                info = it.get("keyword_info") or {}
                props = it.get("keyword_properties") or {}
                kw = it.get("keyword")
                if not kw or kw in vues:
                    continue
                vues[kw] = {"requete": kw, "volume": info.get("search_volume") or 0,
                            "kd": props.get("keyword_difficulty"),
                            "intention": (it.get("search_intent_info") or {}).get("main_intent") or "",
                            "tendance_an_pct": (info.get("search_volume_trend") or {}).get("yearly"), "page": ""}
    lignes = sorted(vues.values(), key=lambda x: -(x["volume"] or 0))
    return {"lieu": lieu, "langue": langue, "graines": graines, "cout_usd": cout, "lignes": lignes}


def cmd_serp(a) -> dict:
    lieu, langue = lieu_et_langue(a)
    if not a.mot:
        raise SystemExit("✗ --mot requis")
    res, cout = appel("serp/google/organic/live/advanced",
                      [{"keyword": a.mot, "location_name": lieu, "language_code": langue, "depth": 10,
                        "people_also_ask_click_depth": 1}])
    organique, questions, associees, aio = [], [], [], False
    for r in res:
        for it in r.get("items") or []:
            t = it.get("type")
            if t == "organic":
                organique.append({"rang": it.get("rank_group"), "url": it.get("url"), "titre": it.get("title"),
                                  "description": it.get("description")})
            elif t == "people_also_ask":
                questions += [q.get("title") for q in it.get("items") or [] if q.get("title")]
            elif t == "related_searches":
                associees += [x for x in it.get("items") or [] if isinstance(x, str)]
            elif t == "ai_overview":
                aio = True
    return {"lieu": lieu, "langue": langue, "mot": a.mot, "cout_usd": cout, "ai_overview": aio,
            "organique": organique[:10], "questions": questions, "recherches_associees": associees}


def main() -> int:
    charger_env()
    ap = argparse.ArgumentParser(description="Demande de recherche par l'API DataForSEO")
    sp = ap.add_subparsers(dest="cmd", required=True)
    for nom in ("volumes", "idees", "serp"):
        p = sp.add_parser(nom)
        p.add_argument("--langue", help="fr, en, ar…")
        p.add_argument("--pays", help="code ISO, défaut : projet.pays_cible")
        p.add_argument("--lieu", help="nom de lieu DataForSEO, pour un pays hors liste")
        p.add_argument("--json", action="store_true")
    sp.choices["volumes"].add_argument("--mots")
    sp.choices["volumes"].add_argument("--fichier")
    sp.choices["idees"].add_argument("--graines")
    sp.choices["idees"].add_argument("--lexique", action="store_true", help="graines tirées de memoire/lexique.csv")
    sp.choices["idees"].add_argument("--max", type=int, default=100, help="par graine")
    sp.choices["idees"].add_argument("--mode", choices=["suggestions", "proches"], default="suggestions")
    sp.choices["idees"].add_argument("--ecrire", action="store_true", help="écrit donnees/demande-<langue>-<date>.csv")
    sp.choices["serp"].add_argument("--mot")
    a = ap.parse_args()

    try:
        res = {"volumes": cmd_volumes, "idees": cmd_idees, "serp": cmd_serp}[a.cmd](a)
    except ErreurAPI as exc:
        print(f"✗ DataForSEO : {exc}", file=sys.stderr)
        return 1

    if a.cmd == "idees" and a.ecrire:
        cible = racine_projet() / "donnees" / f"demande-{res['langue']}-{dt.date.today().isoformat()}.csv"
        cible.parent.mkdir(parents=True, exist_ok=True)
        with cible.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["requete", "volume", "kd", "intention", "tendance_an_pct", "page"])
            w.writeheader()
            w.writerows(res["lignes"])
        print(f"  ✓ {cible.relative_to(racine_projet())} · {len(res['lignes'])} requêtes", file=sys.stderr)

    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    elif a.cmd == "serp":
        print(f"\n  « {res['mot']} » · {res['lieu']} · {res['langue']} · AI Overview : {'oui' if res['ai_overview'] else 'non'}\n")
        for o in res["organique"]:
            print(f"  {o['rang']:>2}. {o['titre']}\n      {o['url']}")
        if res["questions"]:
            print("\n  Autres questions posées :")
            for q in res["questions"]:
                print(f"   - {q}")
        if res["recherches_associees"]:
            print("\n  Recherches associées : " + " · ".join(res["recherches_associees"][:10]))
    else:
        print(f"\n  {res['lieu']} · {res['langue']} · {len(res['lignes'])} requêtes\n")
        for l in res["lignes"][:40]:
            extra = f"  kd {l['kd']}" if l.get("kd") is not None else ""
            extra += f"  {l['intention']}" if l.get("intention") else ""
            print(f"  {l['volume'] or 0:>8}  {l['requete']}{extra}")
    print(f"\n  coût DataForSEO : {res['cout_usd']:.4f} $\n", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
