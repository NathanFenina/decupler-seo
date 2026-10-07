#!/usr/bin/env python3
"""Suivi mensuel : la position réelle de chaque mot-clé principal dans Google,
et la citation de chaque prompt validé par le client dans les moteurs IA.

    python3 suivi.py proposer                       # batterie de prompts proposée depuis la cartographie
    python3 suivi.py positions [--mois AAAA-MM]     # SERP Google en direct (DataForSEO), une ligne par mot-clé
    python3 suivi.py prompts [--mois AAAA-MM]       # prompts au statut « valide », sur les moteurs qui ont une clé
    python3 suivi.py rapport [--mois AAAA-MM]       # mois vs mois précédent → rapports/suivi-AAAA-MM.md

Pourquoi en plus de cartographie.py mensuel : la Search Console donne une
position moyenne, et seulement une fois l'accès ouvert. Ici on relève la
position telle qu'un acheteur la voit le jour du relevé, l'URL qui ranke
(la bonne page ou une autre), le concurrent devant, et la présence d'un AI
Overview. Les deux mesures se complètent ; aucune ne remplace l'autre.

La batterie de prompts vit dans recherche/prompts-suivi.csv :
    id,prompt,famille,funnel,poids,silo,page_cible,statut,source,ajoute_le
- statut : propose → valide (par le client) ou refuse. Seuls les prompts
  valides sont mesurés (--tout pour mesurer aussi les proposés, ex. relevé
  de référence avant validation).
- On ajoute des prompts, on n'en retire jamais : une ligne refusée reste,
  avec son statut, pour qu'elle ne soit pas reproposée.

Historiques (un relevé par mois, relancer le même mois remplace ses lignes) :
    donnees/suivi-positions.csv   donnees/suivi-prompts.csv

Coûts : DataForSEO ~0,002 $ par mot-clé (affiché après l'appel) ; un appel
par prompt et par moteur pour les prompts. Annoncés avant de lancer.
Sans dépendance.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import charger_env, lire_valeur, racine_projet  # noqa: E402

CHAMPS_PROMPTS = ["id", "prompt", "famille", "funnel", "poids", "silo", "page_cible", "statut", "source", "ajoute_le"]
CHAMPS_POS = ["mois", "date", "mot_cle", "url_cible", "position", "url_classee", "bonne_page",
              "devant", "ai_overview", "top3"]
CHAMPS_IA = ["mois", "date", "id", "prompt", "funnel", "silo", "moteur", "cite", "rang", "nomme",
             "concurrents_nommes", "sources"]
POIDS_FUNNEL = {"TOFU": "1", "MOFU": "2", "BOFU": "3"}


# ─── Fonctions pures (testées) ────────────────────────────────────

def domaine(url: str) -> str:
    hote = urllib.parse.urlparse(url if "//" in url else f"https://{url}").netloc.lower()
    return hote.removeprefix("www.")


def chemin(url: str) -> str:
    if not url:
        return ""
    p = urllib.parse.urlparse(url if "//" in url else f"https://x{url if url.startswith('/') else '/' + url}").path
    return (p.rstrip("/") or "/").lower()


def position_dans_serp(organique: list[dict], dom: str, url_cible: str = "") -> dict:
    """Première position du domaine, l'URL classée, si c'est la page visée, qui est devant."""
    dom = domaine(dom)
    devant = []
    for it in organique:
        d = domaine(it.get("url") or "")
        if d == dom or d.endswith("." + dom):
            bonne = (not url_cible) or chemin(it["url"]) == chemin(url_cible)
            return {"position": it.get("rang"), "url_classee": it["url"], "bonne_page": "oui" if bonne else "non",
                    "devant": devant[0] if devant else ""}
        if d and d not in devant:
            devant.append(d)
    return {"position": "", "url_classee": "", "bonne_page": "", "devant": devant[0] if devant else ""}


def fusionner_prompts(existants: list[dict], nouveaux: list[dict]) -> list[dict]:
    """Ajoute sans jamais retirer ni écraser : la clé est le texte du prompt."""
    vus = {e["prompt"].strip().lower() for e in existants}
    sortie = list(existants)
    n = len(existants)
    for p in nouveaux:
        cle = p["prompt"].strip().lower()
        if cle in vus or not cle:
            continue
        n += 1
        ligne = {c: "" for c in CHAMPS_PROMPTS}
        ligne.update(p)
        ligne["id"] = ligne.get("id") or f"P{n:03d}"
        ligne["statut"] = ligne.get("statut") or "propose"
        ligne["poids"] = ligne.get("poids") or POIDS_FUNNEL.get(ligne.get("funnel", "").upper(), "1")
        sortie.append(ligne)
        vus.add(cle)
    return sortie


def remplacer_mois(historique: list[dict], nouvelles: list[dict], mois: str) -> list[dict]:
    return [h for h in historique if h.get("mois") != mois] + nouvelles


def mois_precedent(mois: str) -> str:
    a, m = map(int, mois.split("-"))
    return f"{a - 1}-12" if m == 1 else f"{a}-{m - 1:02d}"


def comparer_positions(hist: list[dict], mois: str) -> list[dict]:
    av = {h["mot_cle"]: h for h in hist if h["mois"] == mois_precedent(mois)}
    lignes = []
    for h in (x for x in hist if x["mois"] == mois):
        p, q = h.get("position"), (av.get(h["mot_cle"]) or {}).get("position")
        delta = (int(q) - int(p)) if (p and q) else None   # positif = places gagnées
        lignes.append({**h, "position_avant": q or "", "delta": delta})
    return sorted(lignes, key=lambda x: (x["position"] == "", int(x["position"] or 999)))


def comparer_prompts(hist: list[dict], mois: str) -> list[dict]:
    def present(r):
        return r.get("cite") in ("True", "1", "oui", True) or r.get("nomme") in ("True", "1", "oui", True)
    av = {(h["id"], h["moteur"]): present(h) for h in hist if h["mois"] == mois_precedent(mois)}
    out = []
    for h in (x for x in hist if x["mois"] == mois):
        avant = av.get((h["id"], h["moteur"]))
        maintenant = present(h)
        evo = "" if avant is None else ("gagné" if maintenant and not avant else "perdu" if avant and not maintenant else "")
        out.append({**h, "present": maintenant, "evolution": evo})
    return out


# ─── Fichiers ─────────────────────────────────────────────────────

def lire(chemin_csv: Path) -> list[dict]:
    if not chemin_csv.exists():
        return []
    with chemin_csv.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def ecrire(chemin_csv: Path, lignes: list[dict], champs: list[str]) -> None:
    chemin_csv.parent.mkdir(parents=True, exist_ok=True)
    with chemin_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs, extrasaction="ignore")
        w.writeheader()
        w.writerows(lignes)


# ─── Commandes ────────────────────────────────────────────────────

def cmd_proposer(a, racine: Path) -> int:
    carto = lire(racine / "memoire" / "cartographie.csv")
    fichier = racine / "recherche" / "prompts-suivi.csv"
    existants = lire(fichier)
    nouveaux = [{"prompt": c["prompt_principal"], "famille": "decouverte", "funnel": c.get("funnel", ""),
                 "silo": c.get("silo", ""), "page_cible": c.get("url", ""), "source": "cartographie",
                 "ajoute_le": dt.date.today().isoformat()}
                for c in carto if c.get("prompt_principal")]
    fusion = fusionner_prompts(existants, nouveaux)
    ecrire(fichier, fusion, CHAMPS_PROMPTS)
    print(f"  {len(fusion) - len(existants)} prompt(s) ajouté(s) au statut « propose » · {len(fusion)} au total → {fichier}")
    print("  Faites valider la liste par le client (statut valide / refuse) avant le premier relevé officiel.")
    return 0


def cmd_positions(a, racine: Path) -> int:
    import demande
    carto = [c for c in lire(racine / "memoire" / "cartographie.csv") if c.get("mot_cle_principal")]
    if a.max:
        carto = carto[: a.max]
    dom = lire_valeur("projet.domaine")
    pays = (lire_valeur("projet.pays_cible") or "FR").upper()
    lieu = demande.LIEUX.get(pays, "France")
    print(f"  {len(carto)} mot(s)-clé(s) · Google {lieu} · ~{len(carto) * 0.002:.2f} $ estimés")
    mois, jour = a.mois, dt.date.today().isoformat()
    lignes, cout = [], 0.0
    for c in carto:
        mot = c["mot_cle_principal"].split("/")[0].strip()
        try:
            res, prix = demande.appel("serp/google/organic/live/advanced",
                                      [{"keyword": mot, "location_name": lieu, "language_code": a.langue, "depth": 50}])
        except demande.ErreurAPI as exc:
            print(f"  ✗ {mot} : {exc}")
            continue
        cout += prix
        organique, aio = [], False
        for r in res:
            for it in r.get("items") or []:
                if it.get("type") == "organic":
                    organique.append({"rang": it.get("rank_group"), "url": it.get("url")})
                elif it.get("type") == "ai_overview":
                    aio = True
        pos = position_dans_serp(organique, dom, c.get("url", ""))
        top3 = " | ".join(domaine(o["url"]) for o in organique[:3])
        lignes.append({"mois": mois, "date": jour, "mot_cle": mot, "url_cible": c.get("url", ""), **pos,
                       "ai_overview": "oui" if aio else "non", "top3": top3})
        print(f"  {str(pos['position'] or '>50'):>4}  {mot[:48]:<48} {'' if pos['bonne_page'] != 'non' else '⚠ autre page'}")
        time.sleep(0.2)
    fichier = racine / "donnees" / "suivi-positions.csv"
    ecrire(fichier, remplacer_mois(lire(fichier), lignes, mois), CHAMPS_POS)
    print(f"  Coût réel : {cout:.3f} $ · {len(lignes)} relevé(s) → {fichier}")
    return 0 if lignes else 1


def cmd_prompts(a, racine: Path) -> int:
    import share_of_model as som
    prompts = lire(racine / "recherche" / "prompts-suivi.csv")
    statuts = {"valide", "propose"} if a.tout else {"valide"}
    prompts = [p for p in prompts if p.get("statut", "propose") in statuts]
    if not prompts:
        print("  Aucun prompt à mesurer (statut « valide »). Lancez « proposer », faites valider, ou ajoutez --tout.")
        return 1
    moteurs = som.moteurs_disponibles([m.strip() for m in a.moteurs.split(",") if m.strip()] or None)
    if not moteurs:
        print("  Aucun moteur disponible (OPENAI_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY, PERPLEXITY_API_KEY).")
        return 1
    marque, dom = lire_valeur("projet.nom"), domaine(lire_valeur("projet.domaine"))
    concurrents = [c.strip() for c in (lire_valeur("projet.concurrents") or []) if str(c).strip()] \
        if isinstance(lire_valeur("projet.concurrents"), list) else []
    print(f"  {len(prompts)} prompt(s) × {', '.join(moteurs)} = {len(prompts) * len(moteurs)} appels")
    mois, jour, lignes = a.mois, dt.date.today().isoformat(), []
    for m in moteurs:
        fn = som.MOTEURS[m][1]
        for p in prompts:
            try:
                rep = fn(p["prompt"], web=True)
            except Exception as exc:  # un moteur en erreur ne doit pas arrêter le relevé
                print(f"  ✗ {m} {p['id']} : {str(exc)[:80]}")
                continue
            r = som.analyser(rep, marque, dom, concurrents)
            lignes.append({"mois": mois, "date": jour, "id": p["id"], "prompt": p["prompt"], "funnel": p.get("funnel", ""),
                           "silo": p.get("silo", ""), "moteur": m, "cite": r["cite"], "rang": r["rang"], "nomme": r["nomme"],
                           "concurrents_nommes": r["concurrents_nommes"], "sources": r["sources"]})
            etat = f"cité #{r['rang']}" if r["cite"] else ("nommé" if r["nomme"] else "absent")
            print(f"  {m:<8} {p['id']:<5} {etat:<9} {p['prompt'][:62]}")
            time.sleep(0.4)
    fichier = racine / "donnees" / "suivi-prompts.csv"
    ecrire(fichier, remplacer_mois(lire(fichier), lignes, mois), CHAMPS_IA)
    print(f"  {len(lignes)} relevé(s) → {fichier}")
    return 0 if lignes else 1


def cmd_rapport(a, racine: Path) -> int:
    pos = comparer_positions(lire(racine / "donnees" / "suivi-positions.csv"), a.mois)
    ia = comparer_prompts(lire(racine / "donnees" / "suivi-prompts.csv"), a.mois)
    top3 = sum(1 for p in pos if p["position"] and int(p["position"]) <= 3)
    p1 = sum(1 for p in pos if p["position"] and int(p["position"]) <= 10)
    par_moteur: dict[str, list[bool]] = {}
    for r in ia:
        par_moteur.setdefault(r["moteur"], []).append(r["present"])
    md = [f"# Suivi {a.mois} — positions et visibilité IA", "",
          f"- Mots-clés suivis : {len(pos)} · top 3 : {top3} · page 1 : {p1}",
          *[f"- {m} : présent sur {sum(v)}/{len(v)} prompts ({100 * sum(v) / len(v):.0f} %)" for m, v in par_moteur.items() if v],
          "", "## Positions Google (relevé direct)", "",
          "| Mot-clé | Position | Mois précédent | Δ | Bonne page | Devant | AIO |", "|---|---|---|---|---|---|---|"]
    for p in pos:
        d = "" if p["delta"] is None else f"{p['delta']:+d}"
        md.append(f"| {p['mot_cle']} | {p['position'] or '>50'} | {p['position_avant'] or '—'} | {d} | "
                  f"{p['bonne_page'] or '—'} | {p['devant'] or '—'} | {p['ai_overview']} |")
    md += ["", "## Prompts suivis", "", "| Prompt | Funnel | Moteur | Présent | Évolution | Concurrents nommés |",
           "|---|---|---|---|---|---|"]
    for r in ia:
        md.append(f"| {r['prompt']} | {r['funnel']} | {r['moteur']} | {'oui' if r['present'] else 'non'} | "
                  f"{r['evolution'] or '—'} | {r['concurrents_nommes'] or '—'} |")
    sortie = racine / "rapports" / f"suivi-{a.mois}.md"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text("\n".join(md) + "\n", encoding="utf-8")
    (racine / "rapports" / f"suivi-{a.mois}.json").write_text(
        json.dumps({"mois": a.mois, "positions": pos, "prompts": ia}, ensure_ascii=False, indent=1, default=str),
        encoding="utf-8")
    print(f"  → {sortie}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Suivi mensuel des positions et des prompts")
    sp = p.add_subparsers(dest="cmd", required=True)
    for nom in ("proposer", "positions", "prompts", "rapport"):
        s = sp.add_parser(nom)
        s.add_argument("--mois", default=f"{dt.date.today():%Y-%m}")
    sp.choices["positions"].add_argument("--max", type=int, default=0)
    sp.choices["positions"].add_argument("--langue", default="fr")
    sp.choices["prompts"].add_argument("--moteurs", default="")
    sp.choices["prompts"].add_argument("--tout", action="store_true", help="mesurer aussi les prompts proposés")
    a = p.parse_args()
    charger_env()
    racine = racine_projet()
    return {"proposer": cmd_proposer, "positions": cmd_positions, "prompts": cmd_prompts,
            "rapport": cmd_rapport}[a.cmd](a, racine)


if __name__ == "__main__":
    sys.exit(main())
