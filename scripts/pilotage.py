#!/usr/bin/env python3
"""
pilotage.py — le tableau de bord partagé de plusieurs projets, et leur roadmap.

Le tableau de bord est une page publiée (Artifact) dont l'état est un bloc JSON
embarqué : <script type="application/json" id="etat">…</script>. Le client ou
le consultant y valide les actions proposées ; les routines le lisent, exécutent
ce qui est validé et y notent ce qu'elles ont fait. Ce script ne touche qu'à ce
bloc : jamais au reste de la page.

    # 1. Les chiffres du projet (Search Console, cartographie, relevés IA)
    python3 pilotage.py donnees --sortie donnees/pilotage.json

    # 2. Les actions du mois, proposées à la validation
    python3 pilotage.py proposer --mois 2026-10 --sortie donnees/actions-2026-10.json

    # 3. Les reporter dans la page (lue auparavant avec l'outil Artifact)
    python3 pilotage.py injecter --html tableau.html --projet-id atlas \\
        --donnees donnees/pilotage.json --actions donnees/actions-2026-10.json

    # 4. Ce qui est validé pour ce projet, et le noter une fois fait
    python3 pilotage.py etat --html tableau.html --projet-id atlas --statut validee
    python3 pilotage.py marquer --html tableau.html --projet-id atlas --id a1b2c3d4 \\
        --statut faite --lien https://github.com/…/pull/12

Une action validée n'est jamais reproposée ni écrasée : l'injection ajoute les
nouvelles propositions et garde les décisions déjà prises.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import charger_env, lire_valeur, racine_projet  # noqa: E402

STATUTS = ("proposee", "validee", "refusee", "en-cours", "faite")
MAX_ACTIONS = 8
BALISE = re.compile(r'(<script type="application/json" id="etat">)(.*?)(</script>)', re.S)


# ─── L'état embarqué dans la page ─────────────────────────────────

def lire_etat(html: str) -> dict:
    m = BALISE.search(html)
    if not m:
        raise SystemExit('✗ bloc <script type="application/json" id="etat"> introuvable dans la page')
    brut = m.group(2).strip()
    return json.loads(brut.replace("<\\/", "</")) if brut else {"projets": []}


def ecrire_etat(html: str, etat: dict) -> str:
    texte = json.dumps(etat, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return BALISE.sub(lambda m: m.group(1) + texte + m.group(3), html, count=1)


def projet_de(etat: dict, pid: str, creer: bool = False) -> dict | None:
    for p in etat.setdefault("projets", []):
        if p.get("id") == pid:
            return p
    if not creer:
        return None
    p = {"id": pid, "actions": []}
    etat["projets"].append(p)
    return p


def id_action(projet: str, type_: str, page: str, requete: str = "") -> str:
    cle = "|".join([projet, type_, page.rstrip("/").lower(), requete.lower()])
    return hashlib.sha1(cle.encode("utf-8")).hexdigest()[:8]


def fusionner_actions(existantes: list[dict], nouvelles: list[dict], date: str) -> tuple[list[dict], int]:
    """Ajoute les nouvelles propositions sans jamais toucher à une décision prise.

    Une action refusée ne revient pas ; une action encore « proposée » est
    rafraîchie (chiffres du mois) ; les autres statuts restent tels quels."""
    par_id = {a["id"]: a for a in existantes}
    ajoutees = 0
    for n in nouvelles:
        a = par_id.get(n["id"])
        if a is None:
            par_id[n["id"]] = {**n, "statut": "proposee", "maj": date}
            existantes.append(par_id[n["id"]])
            ajoutees += 1
        elif a.get("statut") == "proposee":
            a.update({k: v for k, v in n.items() if k not in ("statut", "note", "lien")}, maj=date)
    return existantes, ajoutees


def marquer_action(p: dict, aid: str, statut: str, lien: str = "", note: str = "", date: str = "") -> dict:
    if statut not in STATUTS:
        raise SystemExit(f"✗ statut « {statut} » : attendu {', '.join(STATUTS)}")
    for a in p.get("actions", []):
        if a["id"] == aid:
            a["statut"] = statut
            a["maj"] = date or dt.date.today().isoformat()
            if lien:
                a["lien"] = lien
            if note:
                a["note"] = note
            return a
    raise SystemExit(f"✗ action {aid} introuvable dans le projet {p.get('id')}")


# ─── Les propositions du mois ─────────────────────────────────────

LIBELLES = {
    "ctr": "Réécrire title et meta pour le taux de clic",
    "page-1": "Enrichir la page pour viser le top 3",
    "page-2": "Renforcer la page pour passer en page 1",
    "cannibalisation": "Trancher la cannibalisation (fusion ou redirection)",
    "invisible": "Revoir l'angle, le maillage et les liens de la page",
    "a-creer": "Créer la page",
    "format-special": "Créer un outil ou une ressource",
    "loin": "Refondre la page ou revoir son mot-clé principal",
    "a-verifier": "Vérifier l'indexation et le positionnement",
}
EFFORT = {"ctr": "S", "page-1": "M", "page-2": "M", "cannibalisation": "M", "invisible": "M",
          "a-creer": "L", "format-special": "L", "loin": "L", "a-verifier": "S"}
EXECUTANT = {"ctr": "optimisation", "page-1": "optimisation", "page-2": "optimisation",
             "invisible": "optimisation", "a-verifier": "optimisation", "loin": "optimisation",
             "a-creer": "contenu", "format-special": "contenu", "cannibalisation": "decision"}


def chemin(url: str) -> str:
    """Chemin affiché d'une URL ; vide pour une page qui n'existe pas encore."""
    return (re.sub(r"^https?://[^/]+", "", url) or "/") if url else ""


def depuis_opportunites(res: dict, projet: str, top: int = 6) -> list[dict]:
    """Les meilleures actions du classement (opportunites.py --json), hors pages en mesure."""
    actions, vues = [], set()
    for o in res.get("opportunites", []):
        if not o.get("score") or o.get("en_mesure_jusqu_au"):
            continue
        cle = (o["action"], o.get("page") or o["requete"])
        if cle in vues:
            continue
        vues.add(cle)
        gain = o.get("gain_clics_mois") or 0
        pourquoi = (f"« {o['requete']} » : position {o['position']}, {o.get('impressions_mois', 0)} impressions/mois"
                    if o.get("position") else f"« {o['requete']} » : {int(o.get('volume_mois') or 0)} recherches/mois, "
                    f"le site n'y apparaît pas")
        actions.append({
            "id": id_action(projet, o["action"], o.get("page", ""), o["requete"]),
            "titre": f"{LIBELLES.get(o['action'], o.get('a_faire', o['action']))} — {o['requete']}",
            "type": EXECUTANT.get(o["action"], "optimisation"), "page": chemin(o.get("page", "")),
            "pourquoi": pourquoi, "gain": f"+{round(gain)} clics/mois" if gain >= 1 else "",
            "effort": EFFORT.get(o["action"], "M"), "source": "opportunites"})
        if len(actions) >= top:
            break
    return actions


def depuis_cartographie(carto: dict, projet: str, seuil: float = 3.0) -> list[dict]:
    """Cannibalisations et fortes baisses sur un mot-clé principal (cartographie.py mensuel --json)."""
    actions = []
    for mc, pages in (carto.get("cannibalisation") or {}).items():
        actions.append({"id": id_action(projet, "cannibalisation", "|".join(sorted(pages)), mc),
                        "titre": f"Trancher la cannibalisation — {mc}", "type": "decision",
                        "page": " · ".join(pages), "pourquoi": f"{len(pages)} pages visent « {mc} »",
                        "gain": "", "effort": "M", "source": "cartographie"})
    for l in carto.get("lignes", []):
        d = l.get("delta_position_mc")
        if d is not None and d <= -seuil and not l.get("en_mesure"):
            actions.append({"id": id_action(projet, "baisse", l.get("url", ""), l.get("mot_cle_principal", "")),
                            "titre": f"Diagnostiquer la baisse — {l.get('mot_cle_principal')}", "type": "optimisation",
                            "page": chemin(l.get("url", "")),
                            "pourquoi": f"position {l.get('position_mc_prec')} → {l.get('position_mc')} en un mois",
                            "gain": "", "effort": "S", "source": "cartographie"})
    return actions


def depuis_journal(lignes: list[dict], projet: str) -> list[dict]:
    """Modifications jugées en perte : proposer le retour arrière."""
    return [{"id": id_action(projet, "retour", l.get("url", ""), l.get("id", "")),
             "titre": f"Retour arrière de la modification n° {l.get('id')} ({l.get('type')})", "type": "optimisation",
             "page": chemin(l.get("url", "")), "pourquoi": f"jugée en perte à J+28 : {(l.get('note') or '')[:80]}",
             "gain": "", "effort": "S", "source": "journal"}
            for l in lignes if (l.get("verdict") or "").lower() == "perte"]


def depuis_points_ouverts(texte: str, projet: str) -> list[dict]:
    """Cases non cochées d'un fichier de points ouverts (docs/seo/a-traiter.md, rapports/a-valider.md).

    Une case peut courir sur plusieurs lignes : les lignes indentées qui suivent en font partie."""
    actions = []
    for m in re.finditer(r"^- \[ \] (.+(?:\n[ \t]+\S.*)*)", texte, re.M):
        titre = re.sub(r"\s+", " ", m.group(1)).strip()
        actions.append({"id": id_action(projet, "point", "", titre[:60]), "titre": titre[:200], "type": "decision",
                        "page": "", "pourquoi": "point ouvert", "gain": "", "effort": "M", "source": "points-ouverts"})
    return actions


def sans_doublons(actions: list[dict]) -> list[dict]:
    """Un point ouvert qui redit une cannibalisation déjà proposée (même mot-clé entre guillemets) est écarté."""
    cles = {m.group(1).lower() for a in actions if a.get("source") == "cartographie"
            for m in [re.search(r"— (.+)$", a["titre"])] if m and a["titre"].startswith("Trancher")}
    garde = []
    for a in actions:
        cites = {c.lower() for c in re.findall(r"« ([^»]+?) »", a["titre"])}
        if a.get("source") == "points-ouverts" and cites & cles:
            continue
        garde.append(a)
    return garde


def prioriser(actions: list[dict], maximum: int = MAX_ACTIONS, decisions_max: int = 3) -> list[dict]:
    """Au plus trois décisions humaines (elles débloquent le reste), puis le gain, puis l'effort le plus faible.

    Les décisions en trop reviennent le mois suivant ; elles ne chassent pas les actions chiffrées."""
    def gain(a):
        m = re.search(r"\d+", a.get("gain") or "")
        return int(m.group()) if m else 0
    vues, uniques = set(), []
    for a in actions:
        if a["id"] not in vues:
            vues.add(a["id"])
            uniques.append(a)
    ordre = lambda a: (-gain(a), "SML".find(a.get("effort", "M")))
    decisions = [a for a in uniques if a["type"] == "decision"][:decisions_max]
    autres = sorted((a for a in uniques if a["type"] != "decision"), key=ordre)
    choisies = decisions + autres[:maximum - len(decisions)]
    if len(choisies) < maximum:                      # peu d'actions chiffrées : les décisions restantes complètent
        choisies += [a for a in uniques if a["type"] == "decision" and a not in choisies][:maximum - len(choisies)]
    return choisies


# ─── Les chiffres du projet ───────────────────────────────────────

def serie_hebdo(lignes_date: list[dict], semaines: int = 12) -> list[dict]:
    """Lignes Search Console par jour → clics et impressions par semaine (lundi), les N dernières."""
    par = {}
    for r in lignes_date:
        jour = dt.date.fromisoformat(r["keys"][0][:10])
        lundi = (jour - dt.timedelta(days=jour.weekday())).isoformat()
        s = par.setdefault(lundi, {"semaine": lundi, "clics": 0, "impressions": 0})
        s["clics"] += r.get("clicks", 0)
        s["impressions"] += r.get("impressions", 0)
    return [{**s, "clics": int(s["clics"]), "impressions": int(s["impressions"])}
            for s in sorted(par.values(), key=lambda s: s["semaine"])][-semaines:]


def dernier(racine: Path, motif: str) -> Path | None:
    fichiers = sorted(racine.glob(motif))
    return fichiers[-1] if fichiers else None


def donnees_projet(racine: Path, gsc_lignes: list[dict] | None) -> dict:
    """Les chiffres affichés pour un projet : série hebdo, cartographie du dernier mois, citations IA."""
    d: dict = {"nom": lire_valeur("projet.nom", racine.name), "site": lire_valeur("projet.domaine", ""),
               "maj": dt.date.today().isoformat()}
    if gsc_lignes is not None:
        serie = serie_hebdo(gsc_lignes)
        # La dernière semaine est souvent incomplète (données Search Console à J-2) : on l'écarte des totaux.
        pleines = serie[:-1] if len(serie) > 4 else serie
        d["serie"] = serie
        d["kpis"] = {"clics_4s": sum(s["clics"] for s in pleines[-4:]),
                     "clics_4s_prec": sum(s["clics"] for s in pleines[-8:-4]),
                     "impressions_4s": sum(s["impressions"] for s in pleines[-4:])}
    carto = dernier(racine, "rapports/cartographie-*.json")
    if carto:
        c = json.loads(carto.read_text(encoding="utf-8"))
        s = c.get("synthese", {})
        d.setdefault("kpis", {}).update({
            "pages_suivies": s.get("pages"), "top_10": s.get("top_10"),
            "prompts": f"{s.get('prompts_presents', 0)}/{s.get('prompts_mesures', 0)}" if s.get("prompts_mesures") else "",
            "mois_cartographie": c.get("mois")})
        lignes = [l for l in c.get("lignes", []) if l.get("url")]
        lignes.sort(key=lambda l: ({"P1": 0, "P2": 1}.get(l.get("priorite"), 2),
                                   l.get("position_mc") if l.get("position_mc") is not None else 999))
        d["cartographie"] = [{
            "page": chemin(l["url"]), "mot_cle": l.get("mot_cle_principal", ""),
            "position": l.get("position_mc"), "delta": l.get("delta_position_mc"),
            "prompt": l.get("prompt_principal", ""),
            "ia": {m: l.get(f"ia_{m}") for m in ("openai", "gemini", "claude") if l.get(f"ia_{m}")},
            "action": l.get("action", "")} for l in lignes[:15]]
    return d


def lire_gsc_jours(jours: int = 91) -> list[dict] | None:
    try:
        import gsc
        site = gsc.site_par_defaut()
        fin = dt.date.today() - dt.timedelta(days=2)
        return gsc.requete(site, ["date"], (fin - dt.timedelta(days=jours)).isoformat(), fin.isoformat(), 500)
    except Exception as exc:  # pas d'accès : la page s'affiche sans série
        print(f"  ! Search Console indisponible : {str(exc)[:100]}", file=sys.stderr)
        return None


# ─── Commandes ────────────────────────────────────────────────────

def cmd_donnees(a) -> int:
    racine = racine_projet()
    d = donnees_projet(racine, None if a.sans_gsc else lire_gsc_jours())
    sortie = json.dumps(d, ensure_ascii=False, indent=1)
    if a.sortie:
        Path(a.sortie).write_text(sortie, encoding="utf-8")
        print(f"  ✓ {a.sortie}")
    else:
        print(sortie)
    return 0


def cmd_proposer(a) -> int:
    racine = racine_projet()
    pid = a.projet_id or re.sub(r"[^a-z0-9]+", "-", lire_valeur("projet.nom", racine.name).lower()).strip("-")
    actions: list[dict] = []
    if not a.sans_opportunites:
        demande = dernier(racine, "donnees/demande-*.csv")
        cmd = [sys.executable, str(Path(__file__).parent / "opportunites.py"), "--json"]
        if demande:
            cmd += ["--demande", str(demande)]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=racine, timeout=600)
        if r.returncode == 0 and r.stdout.strip().startswith("{"):
            actions += depuis_opportunites(json.loads(r.stdout), pid)
        else:
            print(f"  ! classement indisponible : {(r.stderr or r.stdout)[-200:]}", file=sys.stderr)
    carto = dernier(racine, "rapports/cartographie-*.json")
    if carto:
        actions += depuis_cartographie(json.loads(carto.read_text(encoding="utf-8")), pid)
    journal = racine / "journal" / "modifications.csv"
    if journal.is_file():
        with journal.open(encoding="utf-8") as f:
            actions += depuis_journal(list(csv.DictReader(f)), pid)
    for fichier in ("docs/seo/a-traiter.md", "rapports/a-valider.md"):
        if (racine / fichier).is_file():
            actions += depuis_points_ouverts((racine / fichier).read_text(encoding="utf-8"), pid)
    mois = a.mois or dt.date.today().strftime("%Y-%m")
    actions = [{**x, "mois": mois} for x in prioriser(sans_doublons(actions), a.max)]
    sortie = json.dumps(actions, ensure_ascii=False, indent=1)
    if a.sortie:
        Path(a.sortie).write_text(sortie, encoding="utf-8")
        print(f"  ✓ {a.sortie} · {len(actions)} action(s) proposée(s)")
    else:
        print(sortie)
    return 0


def cmd_injecter(a) -> int:
    page = Path(a.html)
    html = page.read_text(encoding="utf-8")
    etat = lire_etat(html)
    p = projet_de(etat, a.projet_id, creer=True)
    date = dt.date.today().isoformat()
    if a.donnees:
        d = json.loads(Path(a.donnees).read_text(encoding="utf-8"))
        p.update({k: v for k, v in d.items() if k != "actions"})
    for cle in ("session", "depot"):
        if getattr(a, cle):
            p[cle] = getattr(a, cle)
    ajoutees = 0
    if a.actions:
        nouvelles = json.loads(Path(a.actions).read_text(encoding="utf-8"))
        p["actions"], ajoutees = fusionner_actions(p.setdefault("actions", []), nouvelles, date)
    etat["maj"] = date
    page.write_text(ecrire_etat(html, etat), encoding="utf-8")
    print(f"  ✓ {page} · projet {a.projet_id} · {ajoutees} action(s) ajoutée(s), "
          f"{sum(1 for x in p.get('actions', []) if x.get('statut') == 'proposee')} à valider")
    return 0


def cmd_etat(a) -> int:
    p = projet_de(lire_etat(Path(a.html).read_text(encoding="utf-8")), a.projet_id)
    if p is None:
        raise SystemExit(f"✗ projet {a.projet_id} absent du tableau de bord")
    actions = [x for x in p.get("actions", []) if not a.statut or x.get("statut") == a.statut]
    if a.json:
        print(json.dumps(actions, ensure_ascii=False, indent=1))
        return 0
    for x in actions:
        print(f"  [{x['statut']:<9}] {x['id']}  {x.get('type', ''):<12} {x['titre']}"
              + (f"  ({x['page']})" if x.get("page") else "") + (f"  → {x['note']}" if x.get("note") else ""))
    if not actions:
        print("  aucune action" + (f" « {a.statut} »" if a.statut else ""))
    return 0


def cmd_marquer(a) -> int:
    page = Path(a.html)
    html = page.read_text(encoding="utf-8")
    etat = lire_etat(html)
    p = projet_de(etat, a.projet_id)
    if p is None:
        raise SystemExit(f"✗ projet {a.projet_id} absent du tableau de bord")
    x = marquer_action(p, a.id, a.statut, a.lien or "", a.note or "")
    etat["maj"] = dt.date.today().isoformat()
    page.write_text(ecrire_etat(html, etat), encoding="utf-8")
    print(f"  ✓ {x['id']} → {x['statut']} : {x['titre']}")
    return 0


def main() -> int:
    charger_env()
    ap = argparse.ArgumentParser(description="Tableau de bord partagé et roadmap des projets")
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("donnees", help="chiffres du projet courant, en JSON")
    p.add_argument("--sortie")
    p.add_argument("--sans-gsc", action="store_true")
    p.set_defaults(f=cmd_donnees)
    p = sp.add_parser("proposer", help="actions du mois proposées à la validation")
    p.add_argument("--mois")
    p.add_argument("--projet-id")
    p.add_argument("--max", type=int, default=MAX_ACTIONS)
    p.add_argument("--sans-opportunites", action="store_true")
    p.add_argument("--sortie")
    p.set_defaults(f=cmd_proposer)
    p = sp.add_parser("injecter", help="reporter chiffres et propositions dans la page")
    p.add_argument("--html", required=True)
    p.add_argument("--projet-id", required=True)
    p.add_argument("--donnees")
    p.add_argument("--actions")
    p.add_argument("--session", help="lien de la conversation dédiée au projet")
    p.add_argument("--depot", help="owner/repo")
    p.set_defaults(f=cmd_injecter)
    p = sp.add_parser("etat", help="actions d'un projet")
    p.add_argument("--html", required=True)
    p.add_argument("--projet-id", required=True)
    p.add_argument("--statut", choices=STATUTS)
    p.add_argument("--json", action="store_true")
    p.set_defaults(f=cmd_etat)
    p = sp.add_parser("marquer", help="changer le statut d'une action")
    p.add_argument("--html", required=True)
    p.add_argument("--projet-id", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--statut", required=True, choices=STATUTS)
    p.add_argument("--lien")
    p.add_argument("--note")
    p.set_defaults(f=cmd_marquer)
    a = ap.parse_args()
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
