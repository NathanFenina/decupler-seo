#!/usr/bin/env python3
"""Plafond de dépenses des API payantes : estimer avant l'appel, consigner après, bloquer au-delà du budget du mois.

    python3 budget.py etat                       # dépenses du mois, par outil
    python3 budget.py estimer mcp__dataforseo__api_request --chemin /v3/serp/google/organic/live/advanced
    python3 budget.py consigner dataforseo 0.05 --note "SERP plombier lyon"
    python3 budget.py hook avant < appel.json    # hook PreToolUse (hooks/budget.sh)
    python3 budget.py hook apres < appel.json    # hook PostToolUse

Réglages (config, section seuils) :
  budget_mensuel_usd      plafond du mois pour le projet (vide = pas de plafond, on consigne seulement)
  budget_demander_usd     un appel estimé au-dessus demande une confirmation (défaut 0,50)

Le journal est .seo-decupler/depenses.csv du projet : un projet = un client,
donc la dépense par client se lit directement. DataForSEO renvoie le coût
réel de chaque appel (« cost ») : c'est lui qui est consigné. Pour les
autres outils (Ahrefs, Semrush, Firecrawl, Perplexity), l'appel est compté
sans montant : leur facturation se fait en unités ou en crédits propres.

Tarifs indicatifs DataForSEO, file standard, en dollars par tâche
(https://dataforseo.com/pricing, repris de claude-seo, MIT, Daniel Agrici) :
ils servent à l'estimation, jamais à la facture.

En hook, le script ne bloque jamais par erreur : s'il ne sait pas lire
l'appel, il laisse passer. Il ne bloque (deny) que si le plafond du mois
est dépassé. Sans dépendance (Python 3.9+).
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import dossier_etat, lire_valeur  # noqa: E402

COLONNES = ["date", "outil", "operation", "cout_usd", "estime", "note"]

# (fragment du chemin DataForSEO, coût par tâche) : le premier fragment trouvé gagne.
TARIFS_DATAFORSEO = [
    ("ai_optimization/llm_mentions/search", 0.103),
    ("ai_optimization", 0.05),
    ("serp/", 0.002),
    ("keywords_data/google_trends", 0.01),
    ("keywords_data", 0.05),
    ("dataforseo_labs/google/bulk_keyword_difficulty", 0.01),
    ("dataforseo_labs/google/search_intent", 0.01),
    ("dataforseo_labs/google/domain_rank_overview", 0.01),
    ("dataforseo_labs/google/bulk_traffic_estimation", 0.01),
    ("dataforseo_labs", 0.05),
    ("on_page/lighthouse", 0.02),
    ("on_page", 0.01),
    ("backlinks/bulk_spam_score", 0.01),
    ("backlinks/domain_intersection", 0.05),
    ("backlinks", 0.02),
    ("content_analysis", 0.02),
    ("business_data", 0.05),
    ("merchant", 0.02),
    ("domain_analytics/whois", 0.005),
    ("domain_analytics", 0.01),
]
DEFAUT_DATAFORSEO = 0.05
# Outils payants comptés sans montant (crédits ou unités propres à chaque fournisseur).
NON_CHIFFRES = ("ahrefs", "semrush", "firecrawl", "perplexity", "ubersuggest", "treg", "monid")
GRATUITS = re.compile(r"(docs_|_docs|list_|locations|languages|status|balance|credit|user_limits|auth_status)", re.I)


def fournisseur(outil: str) -> str | None:
    """« mcp__dataforseo__api_request » → dataforseo ; None pour un outil hors budget."""
    nom = outil.lower()
    if "dataforseo" in nom:
        return "dataforseo"
    for f in NON_CHIFFRES:
        if f in nom:
            return f
    return None


def estimer(outil: str, entree: dict | None = None) -> dict:
    """{fournisseur, operation, cout_usd (None si non chiffré ou gratuit), gratuit}."""
    f = fournisseur(outil)
    entree = entree or {}
    if f is None:
        return {"fournisseur": None, "operation": outil, "cout_usd": None, "gratuit": True}
    operation = outil.split("__")[-1]
    if f == "dataforseo":
        chemin = str(entree.get("path") or entree.get("endpoint") or entree.get("chemin") or operation)
        operation = chemin
        if GRATUITS.search(outil) or GRATUITS.search(chemin.rsplit("/", 1)[-1]):
            return {"fournisseur": f, "operation": chemin, "cout_usd": 0.0, "gratuit": True}
        taches = entree.get("data") or entree.get("body") or entree.get("tasks")
        n = len(taches) if isinstance(taches, list) and taches else 1
        prix = next((p for frag, p in TARIFS_DATAFORSEO if frag in chemin), DEFAUT_DATAFORSEO)
        return {"fournisseur": f, "operation": chemin, "cout_usd": round(prix * n, 4), "gratuit": False}
    if GRATUITS.search(operation):
        return {"fournisseur": f, "operation": operation, "cout_usd": 0.0, "gratuit": True}
    return {"fournisseur": f, "operation": operation, "cout_usd": None, "gratuit": False}


def cout_reel(reponse) -> float | None:
    """Le champ « cost » de la réponse DataForSEO (à la racine, sinon la somme des tâches)."""
    texte = reponse if isinstance(reponse, str) else json.dumps(reponse)
    try:
        d = json.loads(texte)
    except ValueError:
        d = None
    if isinstance(d, dict):
        if isinstance(d.get("cost"), (int, float)):
            return float(d["cost"])
        couts = [t.get("cost") for t in d.get("tasks") or [] if isinstance(t, dict)]
        if couts and all(isinstance(c, (int, float)) for c in couts):
            return float(sum(couts))
    m = re.search(r'\\?"cost\\?"\s*:\s*([0-9]+(?:\.[0-9]+)?)', texte)
    return float(m.group(1)) if m else None


def journal() -> Path:
    return dossier_etat("depenses.csv")


def lire_journal(chemin: Path | None = None) -> list[dict]:
    chemin = chemin or journal()
    if not chemin.is_file():
        return []
    with chemin.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def consigner(outil: str, operation: str, cout: float | None, estime: bool, note: str = "",
              chemin: Path | None = None) -> None:
    chemin = chemin or journal()
    chemin.parent.mkdir(parents=True, exist_ok=True)
    neuf = not chemin.is_file()
    with chemin.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES)
        if neuf:
            w.writeheader()
        w.writerow({"date": dt.datetime.now().isoformat(timespec="seconds"), "outil": outil,
                    "operation": operation[:200], "cout_usd": "" if cout is None else f"{cout:.4f}",
                    "estime": "oui" if estime else "non", "note": note[:200]})


def mois(lignes: list[dict], quand: dt.date | None = None) -> dict:
    prefixe = (quand or dt.date.today()).strftime("%Y-%m")
    du_mois = [l for l in lignes if l.get("date", "").startswith(prefixe)]
    par_outil: dict[str, dict] = {}
    for l in du_mois:
        o = par_outil.setdefault(l["outil"], {"appels": 0, "usd": 0.0})
        o["appels"] += 1
        o["usd"] += float(l["cout_usd"]) if l.get("cout_usd") else 0.0
    return {"mois": prefixe, "total_usd": round(sum(o["usd"] for o in par_outil.values()), 4),
            "par_outil": {k: {"appels": v["appels"], "usd": round(v["usd"], 4)} for k, v in par_outil.items()}}


def _nombre(cle: str, defaut: float | None) -> float | None:
    v = lire_valeur(cle, "").replace(",", ".").strip()
    try:
        return float(v) if v else defaut
    except ValueError:
        return defaut


def reglages() -> dict:
    return {"mensuel": _nombre("seuils.budget_mensuel_usd", None),
            "demander": _nombre("seuils.budget_demander_usd", 0.5)}


def decision(est: dict, depense: float, regl: dict) -> tuple[str, str]:
    """(allow | ask | deny, raison) pour un appel estimé."""
    if est["fournisseur"] is None or est["gratuit"]:
        return "allow", ""
    cout = est["cout_usd"]
    if cout is None:
        return "allow", f"{est['fournisseur']} : appel compté (coût en crédits {est['fournisseur']})"
    plafond = regl["mensuel"]
    if plafond is not None and depense + cout > plafond:
        return "deny", (f"Plafond du mois atteint : {depense:.2f} $ dépensés + {cout:.3f} $ estimés > {plafond:.2f} $ "
                        "(seuils.budget_mensuel_usd). Relevez le plafond ou attendez le mois prochain.")
    reste = f", reste {plafond - depense - cout:.2f} $ ce mois" if plafond is not None else ""
    if regl["demander"] is not None and cout > regl["demander"]:
        return "ask", f"{est['fournisseur']} {est['operation']} : environ {cout:.3f} ${reste}. On lance ?"
    return "allow", f"{est['fournisseur']} : ≈ {cout:.3f} ${reste}"


def hook(phase: str, brut: str) -> int:
    try:
        appel = json.loads(brut or "{}")
    except ValueError:
        return 0
    outil = appel.get("tool_name", "")
    est = estimer(outil, appel.get("tool_input") or {})
    if est["fournisseur"] is None:
        return 0
    if phase == "avant":
        choix, raison = decision(est, mois(lire_journal())["total_usd"], reglages())
        if choix == "allow":
            return 0  # pas de sortie : le circuit de permissions habituel s'applique
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": choix,
                                                 "permissionDecisionReason": raison}}, ensure_ascii=False))
        return 0
    if est["gratuit"]:
        return 0
    reel = cout_reel(appel.get("tool_response")) if est["fournisseur"] == "dataforseo" else None
    consigner(est["fournisseur"], est["operation"], reel if reel is not None else est["cout_usd"], reel is None)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Budget des API payantes : estimer, consigner, plafonner")
    sous = ap.add_subparsers(dest="cmd", required=True)
    e = sous.add_parser("etat", help="dépenses du mois par outil")
    e.add_argument("--mois", help="AAAA-MM (défaut : mois en cours)")
    e.add_argument("--json", action="store_true")
    s = sous.add_parser("estimer", help="coût estimé d'un appel")
    s.add_argument("outil", help="nom de l'outil MCP, ex. mcp__dataforseo__api_request")
    s.add_argument("--chemin", default="", help="chemin de l'API DataForSEO")
    s.add_argument("--taches", type=int, default=1)
    c = sous.add_parser("consigner", help="ajouter une dépense faite hors MCP (script, interface)")
    c.add_argument("outil")
    c.add_argument("cout", type=float)
    c.add_argument("--operation", default="manuel")
    c.add_argument("--note", default="")
    h = sous.add_parser("hook", help="hook Claude Code (lit l'appel sur l'entrée standard)")
    h.add_argument("phase", choices=["avant", "apres"])
    a = ap.parse_args()

    if a.cmd == "hook":
        try:
            return hook(a.phase, sys.stdin.read())
        except Exception as ex:  # un hook ne casse jamais la session
            print(f"budget.py : {ex}", file=sys.stderr)
            return 0
    if a.cmd == "estimer":
        est = estimer(a.outil, {"path": a.chemin, "data": [{}] * a.taches} if a.chemin else {})
        print(json.dumps(est, ensure_ascii=False))
        return 0
    if a.cmd == "consigner":
        consigner(a.outil, a.operation, a.cout, False, a.note)
        print(f"✓ {a.outil} {a.cout:.4f} $ consigné dans {journal()}")
        return 0
    quand = dt.date.fromisoformat(a.mois + "-01") if a.mois else None
    m = mois(lire_journal(), quand)
    regl = reglages()
    if a.json:
        print(json.dumps({**m, "plafond_usd": regl["mensuel"]}, ensure_ascii=False, indent=2))
        return 0
    plafond = f" / {regl['mensuel']:.2f} $" if regl["mensuel"] is not None else " (pas de plafond)"
    print(f"Dépenses API {m['mois']} : {m['total_usd']:.3f} ${plafond}")
    for outil, o in sorted(m["par_outil"].items(), key=lambda x: -x[1]["usd"]):
        montant = f"{o['usd']:.3f} $" if o["usd"] else ("crédits du fournisseur" if outil in NON_CHIFFRES else "0 $")
        print(f"  {outil:<12} {o['appels']:>4} appel(s)  {montant}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
