#!/usr/bin/env python3
"""Rapport mensuel d'un projet : les chiffres calculés par un script, pas par l'agent.

    python3 rapport.py                      # mois précédent complet
    python3 rapport.py --mois 2026-09
    python3 rapport.py --mois 2026-09 --json

Écrit rapports/AAAA-MM.json (clés fixes, additionnables entre projets) et
rapports/AAAA-MM.md : la partie factuelle du rapport. L'agent y ajoute ensuite
la lecture — les causes et les décisions —, jamais les chiffres : un chiffre
recalculé à la main dans un texte est un chiffre qui finit faux.

Contenu : trafic du mois contre le mois précédent et le même mois de l'année
précédente, marque et hors marque, pages en hausse et en baisse, requêtes
nouvelles, modifications du mois et verdicts des mesures arrivées à échéance,
exécutions des routines trouvées dans rapports/runs/.

Sans dépendance.
"""

from __future__ import annotations

import argparse
import calendar
import csv
import datetime as dt
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import charger_env, lire_valeur, racine_projet  # noqa: E402


# ─── Périodes ─────────────────────────────────────────────────────

def bornes(mois: str) -> tuple[str, str]:
    a, m = map(int, mois.split("-"))
    return f"{a:04d}-{m:02d}-01", f"{a:04d}-{m:02d}-{calendar.monthrange(a, m)[1]:02d}"


def decaler(mois: str, n: int) -> str:
    a, m = map(int, mois.split("-"))
    t = a * 12 + (m - 1) + n
    return f"{t // 12:04d}-{t % 12 + 1:02d}"


def mois_precedent(aujourdhui: dt.date | None = None) -> str:
    d = (aujourdhui or dt.date.today()).replace(day=1) - dt.timedelta(days=1)
    return f"{d.year:04d}-{d.month:02d}"


# ─── Calculs purs (testés) ────────────────────────────────────────

def variation(nouveau: float, ancien: float) -> float | None:
    return round((nouveau - ancien) / ancien * 100, 1) if ancien else None


def totaux(lignes: list[dict]) -> dict:
    clics = sum(l["clics"] for l in lignes)
    impr = sum(l["impressions"] for l in lignes)
    pos = sum(l["position"] * l["impressions"] for l in lignes) / impr if impr else 0.0
    return {"clics": round(clics), "impressions": round(impr), "ctr_pct": round(clics / impr * 100, 2) if impr else 0.0,
            "position_moyenne": round(pos, 1)}


def ecarts(avant: list[dict], apres: list[dict], cle: str, n: int = 8) -> dict:
    """Plus fortes hausses et baisses de clics (à défaut d'impressions) entre deux périodes."""
    a = {l[cle]: l for l in avant}
    b = {l[cle]: l for l in apres}
    lignes = []
    for k in set(a) | set(b):
        ca, cb = a.get(k, {}).get("clics", 0), b.get(k, {}).get("clics", 0)
        ia, ib = a.get(k, {}).get("impressions", 0), b.get(k, {}).get("impressions", 0)
        lignes.append({cle: k, "clics_avant": round(ca), "clics": round(cb), "delta_clics": round(cb - ca),
                       "impressions_avant": round(ia), "impressions": round(ib), "delta_impressions": round(ib - ia)})
    tri = lambda l: (l["delta_clics"], l["delta_impressions"])  # noqa: E731
    lignes.sort(key=tri)
    baisses = [l for l in lignes if tri(l) < (0, 0)][:n]
    hausses = [l for l in reversed(lignes) if tri(l) > (0, 0)][:n]
    return {"hausses": hausses, "baisses": baisses}


def requetes_nouvelles(avant: list[dict], apres: list[dict], n: int = 15) -> list[dict]:
    connues = {l["requete"] for l in avant}
    neuves = [l for l in apres if l["requete"] not in connues]
    return sorted(neuves, key=lambda l: -l["impressions"])[:n]


def separer_marque(lignes: list[dict], motifs: list[re.Pattern]) -> tuple[dict, dict]:
    marque = [l for l in lignes if any(m.search(l["requete"]) for m in motifs)]
    autres = [l for l in lignes if not any(m.search(l["requete"]) for m in motifs)]
    return totaux(marque), totaux(autres)


def bilan_journal(journal: list[dict], mois: str) -> dict:
    faites = [l for l in journal if l.get("date", "").startswith(mois)]
    mesurees = [l for l in journal if l.get("date_mesure", "").startswith(mois) and l.get("verdict")]
    verdicts = Counter(l["verdict"] for l in mesurees)
    return {"modifications": len(faites), "par_type": dict(Counter(l.get("type", "") for l in faites)),
            "mesurees": len(mesurees), "gains": verdicts.get("gain", 0), "neutres": verdicts.get("neutre", 0),
            "pertes": verdicts.get("perte", 0), "insuffisants": verdicts.get("insuffisant", 0),
            "pertes_detail": [{"id": l.get("id"), "url": l.get("url"), "type": l.get("type")}
                              for l in mesurees if l["verdict"] == "perte"]}


JOUR_HEBDO = 2  # mercredi (calendar : lundi = 0)
BRANCHE_RUN = re.compile(r"(?:^|/)(hebdo|veille|optimisation|contenu|rapport)[-/](\d{4}-\d\d-\d\d)$")


def runs_des_branches(refs: list[str]) -> list[str]:
    """Branches poussées par les routines (claude/veille-AAAA-MM-JJ, contenu/AAAA-MM-JJ…) → noms de journaux.

    Chaque routine travaille sur sa propre branche : son journal de run n'arrive
    sur la branche principale qu'à la fusion. La branche prouve déjà l'exécution."""
    noms = []
    for ref in refs:
        m = BRANCHE_RUN.search(ref.strip())
        if m:
            noms.append(f"{m.group(2)}-{m.group(1)}.md")
    return noms


def branches_distantes(racine: Path) -> list[str]:
    try:
        sortie = subprocess.run(["git", "-C", str(racine), "ls-remote", "--heads", "origin"],
                                capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    return [ligne.split("refs/heads/", 1)[-1] for ligne in sortie.splitlines() if "refs/heads/" in ligne]


def bilan_runs(noms: list[str], mois: str) -> dict:
    """Exécutions trouvées dans rapports/runs/ (fichiers AAAA-MM-JJ-<mode>.md)."""
    compte = Counter()
    jours_hebdo: Counter = Counter()
    for n in noms:
        m = re.match(rf"^{re.escape(mois)}-(\d\d)-([a-z-]+)\.md$", n)
        if m:
            compte[m.group(2)] += 1
            if m.group(2) == "hebdo":
                jours_hebdo[int(m.group(1))] += 1
    a, mm = map(int, mois.split("-"))
    jours = calendar.monthrange(a, mm)[1]
    if compte.get("hebdo") and not compte.get("veille"):
        # Rythme hebdo : un passage par semaine, le jour où la routine tourne
        # (déduit des passages trouvés ; mercredi par défaut), au lieu d'une veille par jour.
        jours_semaine = Counter(calendar.weekday(a, mm, j) for j in jours_hebdo.elements())
        jour = jours_semaine.most_common(1)[0][0] if jours_semaine else JOUR_HEBDO
        attendus = sum(1 for j in range(1, jours + 1) if calendar.weekday(a, mm, j) == jour)
        return {"trouves": dict(compte), "mode": "hebdo", "veille_attendues": attendus,
                "veille_trouvees": compte["hebdo"]}
    return {"trouves": dict(compte), "mode": "veille", "veille_attendues": jours, "veille_trouvees": compte.get("veille", 0)}


def cartographie(racine: Path, mois: str) -> dict | None:
    """Synthèse de la cartographie du mois (cartographie.py mensuel), None s'il n'y en a pas."""
    try:
        import cartographie as carto
        return carto.resume_pour_rapport(racine, mois)
    except Exception as exc:  # un historique abîmé ne doit pas empêcher le rapport
        print(f"  ! cartographie illisible : {exc}", file=sys.stderr)
        return None


def decimale(v: float | None, signe: bool = False) -> str:
    return "n.d." if v is None else (f"{v:+.1f}" if signe else f"{v:.1f}").replace(".", ",")


def section_cartographie(c: dict | None) -> list[str]:
    """Résumé Markdown : gains et pertes sur les mots-clés principaux, prompts gagnés et perdus."""
    if not c:
        return []
    l = ["## Cartographie : mots-clés et prompts principaux", ""]
    if c.get("pages") is None:
        return l + [f"Tableau du mois : `{c['fichier']}` (historique absent : relancer `cartographie.py mensuel`).", ""]
    l += [f"{c['pages']} page(s) suivie(s), {c['a_creer']} à créer. Sur leur mot-clé principal : "
          f"{c['en_hausse']} en hausse, {c['en_baisse']} en baisse, {c['top_10']} en page 1. "
          f"Prompts principaux : site présent sur {c['prompts_presents']} des {c['prompts_mesures']} mesuré(s), "
          f"{len(c['prompts_gagnes'])} gagné(s) et {len(c['prompts_perdus'])} perdu(s) ce mois-ci"
          + (f" (relevé IA {c['mesure_ia']})" if c.get("mesure_ia") else "") + "."
          + (f" Détail : `{c['fichier']}`." if c.get("fichier") else ""), ""]
    lignes = [("hausse", x) for x in c["hausses"]] + [("baisse", x) for x in c["baisses"]]
    if lignes:
        l += ["| | Page | Mot-clé principal | Position | Δ places |", "|---|---|---|---|---|"]
        for sens, x in lignes:
            l.append(f"| {sens} | {x['url'].split('://', 1)[-1]} | {x['mot_cle_principal']} | "
                     f"{decimale(x['position_mc_prec'])} → {decimale(x['position_mc'])} "
                     f"| {decimale(x['delta_position_mc'], signe=True)} |")
        l.append("")
    for titre, cle in (("Prompts gagnés", "prompts_gagnes"), ("Prompts perdus", "prompts_perdus")):
        if c.get(cle):
            l += [f"{titre} : " + " ; ".join(f"« {x['prompt_principal']} »" for x in c[cle]) + ".", ""]
    return l


def a_valider(texte: str) -> int:
    """Entrées ouvertes de rapports/a-valider.md : les lignes de liste non cochées."""
    return len(re.findall(r"^\s*[-*] (?!\[x\])", texte, re.M))


# ─── Collecte ─────────────────────────────────────────────────────

def lire_gsc(site: str, mois: str, dims: list[str]) -> list[dict]:
    import gsc
    debut, fin = bornes(mois)
    cle = {"page": "page", "query": "requete"}
    lignes = []
    for r in gsc.requete(site, dims, debut, fin, 25000):
        l = {"clics": r["clicks"], "impressions": r["impressions"], "position": r["position"]}
        for i, d in enumerate(dims):
            l[cle[d]] = r["keys"][i]
        lignes.append(l)
    return lignes


def collecter(mois: str, site: str | None) -> dict:
    import gsc
    import opportunites
    site = site or gsc.site_par_defaut()
    racine = racine_projet()
    precedent, an_passe = decaler(mois, -1), decaler(mois, -12)

    total = totaux(lire_gsc(site, mois, []))
    total_prec = totaux(lire_gsc(site, precedent, []))
    total_an = totaux(lire_gsc(site, an_passe, []))
    pages, pages_prec = lire_gsc(site, mois, ["page"]), lire_gsc(site, precedent, ["page"])
    req, req_prec = lire_gsc(site, mois, ["query"]), lire_gsc(site, precedent, ["query"])
    marque, hors_marque = separer_marque(req, opportunites.motifs_marque())

    journal = []
    chemin_j = racine / "journal" / "modifications.csv"
    if chemin_j.is_file():
        with chemin_j.open(encoding="utf-8") as f:
            journal = list(csv.DictReader(f))
    runs_dir = racine / "rapports" / "runs"
    noms = [p.name for p in runs_dir.glob("*.md")] if runs_dir.is_dir() else []
    fichier_av = racine / "rapports" / "a-valider.md"

    return {"projet": lire_valeur("projet.nom", racine.name), "mois": mois, "site": site,
            "trafic": {"mois": total, "mois_precedent": total_prec, "an_passe": total_an,
                       "clics_variation_pct": variation(total["clics"], total_prec["clics"]),
                       "clics_variation_an_pct": variation(total["clics"], total_an["clics"]),
                       "impressions_variation_pct": variation(total["impressions"], total_prec["impressions"])},
            "marque": marque, "hors_marque": hors_marque,
            "pages": ecarts(pages_prec, pages, "page"),
            "requetes": ecarts(req_prec, req, "requete"),
            "requetes_nouvelles": requetes_nouvelles(req_prec, req),
            "journal": bilan_journal(journal, mois),
            "runs": bilan_runs(sorted(set(noms) | set(runs_des_branches(branches_distantes(racine)))), mois),
            "a_valider": a_valider(fichier_av.read_text(encoding="utf-8")) if fichier_av.is_file() else 0,
            "cartographie": cartographie(racine, mois)}


# ─── Sorties ──────────────────────────────────────────────────────

def json_standard(r: dict) -> dict:
    """Les clés fixes du rapport, additionnables d'un projet à l'autre (voir seo-cycle)."""
    t, j = r["trafic"], r["journal"]
    return {"projet": r["projet"], "mois": r["mois"], "clics": t["mois"]["clics"],
            "impressions": t["mois"]["impressions"], "position_moyenne": t["mois"]["position_moyenne"],
            "clics_variation_pct": t["clics_variation_pct"], "modifications": j["modifications"],
            "gains": j["gains"], "neutres": j["neutres"], "pertes": j["pertes"], "a_valider": r["a_valider"],
            "runs_attendus": r["runs"]["veille_attendues"], "runs_trouves": r["runs"]["veille_trouvees"],
            # Ajoutée après coup : None quand le projet n'a pas de cartographie. Les clés ci-dessus ne bougent pas.
            "cartographie": r.get("cartographie"),
            "detail": r}


def anonymes(r: dict) -> int:
    """Google masque les requêtes rares : leur part n'apparaît que dans le total du site."""
    return max(0, r["trafic"]["mois"]["impressions"] - r["marque"]["impressions"] - r["hors_marque"]["impressions"])


def pct(v: float | None) -> str:
    return "n.d." if v is None else f"{v:+.1f} %".replace(".", ",")


def markdown(r: dict) -> str:
    t = r["trafic"]
    m, p, a = t["mois"], t["mois_precedent"], t["an_passe"]
    l = [f"# Rapport SEO — {r['projet']} — {r['mois']}", "",
         "> Chiffres calculés par `rapport.py` depuis Search Console et le journal. "
         "Ne pas les modifier à la main : relancer le script.", ""]
    if r["runs"]["veille_trouvees"] < r["runs"]["veille_attendues"]:
        unite = ("passages hebdo trouvés sur", "semaines") if r["runs"].get("mode") == "hebdo" else ("veilles trouvées sur", "jours")
        l += [f"**⚠️ Routines : {r['runs']['veille_trouvees']} {unite[0]} "
              f"{r['runs']['veille_attendues']} {unite[1]}.** Détail : {r['runs']['trouves'] or 'aucune exécution'}.", ""]
    l += ["## Trafic organique", "",
          "| | Mois | Mois précédent | Même mois, an passé |", "|---|---|---|---|",
          f"| Clics | {m['clics']} | {p['clics']} ({pct(t['clics_variation_pct'])}) | {a['clics']} ({pct(t['clics_variation_an_pct'])}) |",
          f"| Impressions | {m['impressions']} | {p['impressions']} ({pct(t['impressions_variation_pct'])}) | {a['impressions']} |",
          f"| CTR | {m['ctr_pct']} % | {p['ctr_pct']} % | {a['ctr_pct']} % |",
          f"| Position moyenne | {m['position_moyenne']} | {p['position_moyenne']} | {a['position_moyenne']} |", "",
          f"Marque : {r['marque']['clics']} clics, {r['marque']['impressions']} impressions. "
          f"Hors marque : {r['hors_marque']['clics']} clics, {r['hors_marque']['impressions']} impressions — "
          "c'est la part que le SEO fait réellement gagner. "
          f"Requêtes anonymisées par Google (non attribuables) : {anonymes(r)} impressions.", ""]
    for titre, bloc, cle in (("Pages en hausse", r["pages"]["hausses"], "page"),
                             ("Pages en baisse", r["pages"]["baisses"], "page"),
                             ("Requêtes en hausse", r["requetes"]["hausses"], "requete"),
                             ("Requêtes en baisse", r["requetes"]["baisses"], "requete")):
        if bloc:
            l += [f"## {titre}", "", "| | Clics | Δ clics | Impressions | Δ impressions |", "|---|---|---|---|---|"]
            l += [f"| {x[cle].split('://', 1)[-1]} | {x['clics']} | {x['delta_clics']:+d} | {x['impressions']} | "
                  f"{x['delta_impressions']:+d} |" for x in bloc]
            l.append("")
    if r["requetes_nouvelles"]:
        l += ["## Requêtes apparues ce mois-ci", "", "| Requête | Impressions | Position |", "|---|---|---|"]
        l += [f"| {x['requete']} | {round(x['impressions'])} | {round(x['position'], 1)} |" for x in r["requetes_nouvelles"]]
        l.append("")
    l += section_cartographie(r.get("cartographie"))
    j = r["journal"]
    l += ["## Modifications et mesures", "",
          f"{j['modifications']} modification(s) publiée(s) ce mois-ci"
          + (f" ({', '.join(f'{k} : {v}' for k, v in j['par_type'].items())})" if j["par_type"] else "") + ". "
          f"{j['mesurees']} mesure(s) arrivée(s) à échéance : {j['gains']} gain(s), {j['neutres']} neutre(s), "
          f"{j['pertes']} perte(s), {j['insuffisants']} insuffisante(s).", ""]
    if j["pertes_detail"]:
        l += ["Pertes, proposées au retour arrière : " + ", ".join(f"#{x['id']} {x['type']} {x['url']}" for x in j["pertes_detail"]), ""]
    l += [f"{r['a_valider']} point(s) en attente dans `rapports/a-valider.md`.", "",
          "## Lecture et décisions", "",
          "<!-- À rédiger par l'agent : les causes (pas seulement les courbes), ce qui a marché, "
          "ce qu'on arrête, les 5 actions du mois prochain (opportunites.py). -->", ""]
    return "\n".join(l)


def main() -> int:
    charger_env()
    ap = argparse.ArgumentParser(description="Rapport mensuel chiffré du projet")
    ap.add_argument("--mois", help="AAAA-MM (défaut : mois précédent)")
    ap.add_argument("--site", help="propriété Search Console (défaut : config du projet)")
    ap.add_argument("--json", action="store_true", help="afficher le JSON sans écrire de fichier")
    a = ap.parse_args()
    mois = a.mois or mois_precedent()
    if not re.fullmatch(r"\d{4}-\d{2}", mois):
        raise SystemExit("✗ --mois attend AAAA-MM")
    try:
        r = collecter(mois, a.site)
    except Exception as exc:  # ErreurGSC, réseau
        print(f"✗ Search Console indisponible : {exc}", file=sys.stderr)
        return 1
    std = json_standard(r)
    if a.json:
        print(json.dumps(std, ensure_ascii=False, indent=1))
        return 0
    dossier = racine_projet() / "rapports"
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / f"{mois}.json").write_text(json.dumps(std, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    cible = dossier / f"{mois}.md"
    if cible.exists():
        # La lecture rédigée par l'agent est conservée : on ne remplace que la partie chiffrée.
        ancien = cible.read_text(encoding="utf-8")
        lecture = ancien[ancien.find("## Lecture et décisions"):] if "## Lecture et décisions" in ancien else ""
        texte = markdown(r)
        if lecture:
            texte = texte[:texte.find("## Lecture et décisions")] + lecture
        cible.write_text(texte, encoding="utf-8")
    else:
        cible.write_text(markdown(r), encoding="utf-8")
    print(f"  ✓ rapports/{mois}.md et rapports/{mois}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
