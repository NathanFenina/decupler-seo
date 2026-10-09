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

    # 5. Le bilan de la semaine dans l'onglet du mois, puis la copie de sûreté dans git
    python3 pilotage.py mois --html tableau.html --projet-id atlas --fichier donnees/semaine.json
    python3 pilotage.py sauvegarder --html tableau.html --projet-id atlas

    # 6. Programmer une action dans un mois à venir, consigner un lien obtenu
    python3 pilotage.py mois-cible --html tableau.html --projet-id atlas --id a1b2c3d4 --mois 2026-12
    python3 pilotage.py lien --html tableau.html --projet-id atlas --url https://media.example/article \
        --cible /audit-geo/ --ancre "audit GEO" --prix 180 --attribut dofollow --statut en-ligne

    # 7. Le plan de netlinking mois par mois (vue Backlinks), l'en-tête et les phases du programme
    python3 pilotage.py backlinks --html tableau.html --projet-id atlas --fichier donnees/backlinks.json
    python3 pilotage.py programme --html tableau.html --projet-id atlas --fichier donnees/programme.json

La page est un programme sur plusieurs mois : synthèse (chiffres du dernier
bilan, décisions urgentes, avancement par chantier), à décider (bloqué, puis à
valider par chantier), roadmap chantier × mois, plan d'actions filtrable,
backlinks (`liens`) et reporting mois par mois. Le mois d'une action est son
`mois_cible` s'il existe, sinon son `mois`. Chaque mercredi, la routine hebdo y
écrit la semaine.

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
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import charger_env, lire_valeur, racine_projet  # noqa: E402

STATUTS = ("proposee", "validee", "refusee", "en-cours", "bloquee", "faite")
MAX_ACTIONS = 8
# Les chantiers rangent la roadmap dans la page (onglet du mois, « à faire »).
CHANTIERS = ("contenus", "optimisation", "technique", "off-page", "geo", "international",
             "securite", "indexation", "design", "pilotage")
SAUVEGARDE = "journal/pilotage.json"
MOIS = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
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
    html = BALISE.sub(lambda m: m.group(1) + texte + m.group(3), html, count=1)
    if etat.get("titre"):                            # le nom de la page suit l'état (onglet, galerie)
        titre = etat["titre"].replace("&", "&amp;").replace("<", "&lt;")
        html = re.sub(r"<title>[^<]*</title>", lambda m: f"<title>{titre}</title>", html, count=1)
    return html


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
            a.update({k: v for k, v in n.items() if k not in ("statut", "note", "lien", "mois_cible")}, maj=date)
    return existantes, ajoutees


def marquer_action(p: dict, aid: str, statut: str, lien: str = "", note: str = "", date: str = "",
                   attend: str = "") -> dict:
    """Change le statut d'une action. « bloquee » dit qui ou quoi on attend (`attend`) ;
    l'attente est effacée dès que l'action repart."""
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
            if statut == "bloquee":
                if attend:
                    a["attend"] = attend
            else:
                a.pop("attend", None)
            return a
    raise SystemExit(f"✗ action {aid} introuvable dans le projet {p.get('id')}")


def mois_valide(mois: str) -> str:
    if not MOIS.match(mois or ""):
        raise SystemExit(f"✗ mois « {mois} » : attendu AAAA-MM")
    return mois


def programmer_action(p: dict, aid: str, mois: str | None) -> dict:
    """Range une action dans un mois de la roadmap (`mois_cible`, AAAA-MM) ; None la rend à son mois d'origine.

    Une action validée programmée plus tard n'est pas exécutée avant son mois (`etat --statut`)."""
    for a in p.get("actions", []):
        if a["id"] == aid:
            if mois is None:
                a.pop("mois_cible", None)
            else:
                a["mois_cible"] = mois_valide(mois)
            return a
    raise SystemExit(f"✗ action {aid} introuvable dans le projet {p.get('id')}")


def mois_prevu(a: dict) -> str:
    """Le mois d'une action dans la roadmap : `mois_cible`, sinon `mois`."""
    return a.get("mois_cible") or a.get("mois") or (a.get("maj") or "")[:7]


def plus_tard(a: dict, mois: str | None = None) -> bool:
    """Action encore ouverte, programmée après le mois en cours."""
    mois = mois or dt.date.today().strftime("%Y-%m")
    return a.get("statut") not in ("faite", "refusee") and mois_prevu(a) > mois


def prix_de(texte: str | float | None) -> float | int | None:
    """« 180 », « 180,50 € », « 1 200 » → nombre ; vide → None."""
    if texte in (None, ""):
        return None
    brut = re.sub(r"[\s\u00a0\u202f€]|EUR", "", str(texte), flags=re.I).replace(",", ".")
    try:
        n = float(brut)
    except ValueError:
        raise SystemExit(f"✗ prix « {texte} » : attendu un nombre (ex. 180 ou 180,50)")
    return int(n) if n.is_integer() else round(n, 2)


def ajouter_lien(p: dict, lien: dict) -> tuple[dict, bool]:
    """Consigne un lien obtenu dans `projet.liens`. Une URL déjà consignée est mise à jour, jamais dupliquée."""
    url = (lien.get("url") or "").strip()
    if not re.match(r"^https?://", url, re.I):
        raise SystemExit(f"✗ URL « {url} » : attendu http(s)://…")
    if not lien.get("domaine"):
        lien["domaine"] = re.sub(r"^www\.", "", urlparse(url).netloc.lower())
    date = lien.get("date") or dt.date.today().isoformat()
    try:
        dt.date.fromisoformat(date)
    except ValueError:
        raise SystemExit(f"✗ date « {date} » : attendu AAAA-MM-JJ")
    lien = {**lien, "url": url, "date": date}
    liens = p.setdefault("liens", [])
    cle = url.rstrip("/").lower()
    for l in liens:
        if (l.get("url") or "").rstrip("/").lower() == cle:
            l.update({k: v for k, v in lien.items() if v not in (None, "")})
            return l, False
    lien = {k: v for k, v in lien.items() if v not in (None, "")}
    liens.append(lien)
    liens.sort(key=lambda l: l.get("date", ""))
    return lien, True


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


def chantier_de(a: dict) -> str:
    """Chantier d'une action proposée par le script, quand elle n'en a pas."""
    if a.get("chantier") in CHANTIERS:
        return a["chantier"]
    if a.get("type") == "contenu":
        return "contenus"
    if a.get("type") == "technique":
        return "technique"
    if a.get("source") == "points-ouverts":
        return "pilotage"
    return "optimisation"


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
    actions = [{**x, "mois": mois, "chantier": chantier_de(x)} for x in prioriser(sans_doublons(actions), a.max)]
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
    if a.titre:
        etat["titre"] = a.titre
    if a.livrables:
        p["livrables"] = json.loads(Path(a.livrables).read_text(encoding="utf-8"))
    if a.theme:
        p["theme"] = json.loads(Path(a.theme).read_text(encoding="utf-8"))
    ajoutees = 0
    if a.actions:
        nouvelles = json.loads(Path(a.actions).read_text(encoding="utf-8"))
        p["actions"], ajoutees = fusionner_actions(p.setdefault("actions", []), nouvelles, date)
    etat["maj"] = date
    page.write_text(ecrire_etat(html, etat), encoding="utf-8")
    print(f"  ✓ {page} · projet {a.projet_id} · {ajoutees} action(s) ajoutée(s), "
          f"{sum(1 for x in p.get('actions', []) if x.get('statut') == 'proposee')} à valider")
    return 0


def corps_de(html: str) -> tuple[str, str]:
    """(titre, contenu) d'une page publiée : ce qui est entre <body> et </body>, sans sa balise <title>."""
    m = re.search(r"<body[^>]*>(.*)</body>", html, re.S | re.I)
    corps = m.group(1) if m else html
    t = re.search(r"<title>([^<]*)</title>", corps, re.I)
    titre = t.group(1).strip() if t else ""
    return titre, re.sub(r"<title>[^<]*</title>\s*", "", corps, count=1, flags=re.I).strip()


def integrer(gabarit: str, hote_html: str, etat: dict) -> str:
    """Page de suivi logée dans une page existante : le tableau de bord en tête, le contenu d'origine dessous, intact.

    Le contenu d'origine est rangé dans <template id="hote"> : la page le rend, et le republie tel quel à chaque
    validation. Le fond de page reste celui de l'hôte."""
    titre, contenu = corps_de(hote_html)
    if 'id="hote"' in hote_html:                     # déjà intégrée : on repart de son contenu d'origine
        avant = hote_html.split('<script type="application/json" id="etat">', 1)[0]   # jamais le code de la page
        m = re.search(r'<template id="hote">(.*?)</template>', avant, re.S)
        if m:
            contenu = m.group(1)
        elif BALISE.search(hote_html):                # page de suivi sans contenu hôte : rien à conserver
            contenu = ""
    if "</template>" in contenu:
        raise SystemExit("✗ la page hôte contient déjà une balise <template> : intégration manuelle requise")
    html = re.sub(r'<style id="css-page">.*?</style>\n?', "", gabarit, count=1, flags=re.S)
    html = html.replace('<script type="application/json" id="etat">',
                        f'<template id="hote">{contenu}</template>\n<script type="application/json" id="etat">', 1)
    etat = {**etat, "titre": etat.get("titre") or titre}
    return ecrire_etat(html, etat)


def cmd_integrer(a) -> int:
    gabarit = (Path(__file__).resolve().parent.parent / "templates" / "pilotage.html").read_text(encoding="utf-8")
    etat = lire_etat(Path(a.etat_depuis).read_text(encoding="utf-8")) if a.etat_depuis else {"projets": []}
    if a.titre:
        etat["titre"] = a.titre
    sortie = integrer(gabarit, Path(a.hote).read_text(encoding="utf-8"), etat)
    Path(a.sortie).write_text(sortie, encoding="utf-8")
    print(f"  ✓ {a.sortie} · contenu de {a.hote} conservé sous le tableau de bord")
    return 0


def cmd_ajouter(a) -> int:
    """Consigne une action décidée ou faite hors des propositions du mois (depuis n'importe quelle conversation)."""
    page = Path(a.html)
    html = page.read_text(encoding="utf-8")
    etat = lire_etat(html)
    p = projet_de(etat, a.projet_id, creer=True)
    date = a.date or dt.date.today().isoformat()
    action = {"id": id_action(a.projet_id, "manuel", a.page or "", a.titre[:60]), "titre": a.titre, "type": a.type,
              "page": a.page or "", "pourquoi": a.pourquoi or "", "gain": a.gain or "", "effort": a.effort,
              "source": "conversation", "mois": date[:7], "statut": a.statut, "maj": date,
              "chantier": a.chantier or chantier_de({"type": a.type})}
    for cle in ("lien", "note", "attend", "qui"):
        if getattr(a, cle):
            action[cle] = getattr(a, cle)
    if a.mois_cible:
        action["mois_cible"] = mois_valide(a.mois_cible)
    existante = next((x for x in p.setdefault("actions", []) if x["id"] == action["id"]), None)
    if existante:
        existante.update({k: v for k, v in action.items() if v})
    else:
        p["actions"].append(action)
    etat["maj"] = date
    page.write_text(ecrire_etat(html, etat), encoding="utf-8")
    print(f"  ✓ {action['id']} [{a.statut}] {a.titre}")
    return 0


def cmd_etat(a) -> int:
    p = projet_de(lire_etat(Path(a.html).read_text(encoding="utf-8")), a.projet_id)
    if p is None:
        raise SystemExit(f"✗ projet {a.projet_id} absent du tableau de bord")
    actions = [x for x in p.get("actions", []) if not a.statut or x.get("statut") == a.statut]
    if a.statut and not a.toutes:                    # une action programmée plus tard attend son mois
        tard = [x for x in actions if plus_tard(x)]
        actions = [x for x in actions if not plus_tard(x)]
        if tard:
            print(f"  ({len(tard)} action(s) « {a.statut} » programmée(s) plus tard, non listée(s) : --toutes pour les voir)",
                  file=sys.stderr)
    if a.json:
        print(json.dumps(actions, ensure_ascii=False, indent=1))
        return 0
    for x in actions:
        print(f"  [{x['statut']:<9}] {x['id']}  {x.get('type', ''):<12} {x['titre']}"
              + (f"  ({x['page']})" if x.get("page") else "") + (f"  · prévue {x['mois_cible']}" if x.get("mois_cible") else "")
              + (f"  → {x['note']}" if x.get("note") else ""))
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
    x = marquer_action(p, a.id, a.statut, a.lien or "", a.note or "", attend=a.attend or "")
    etat["maj"] = dt.date.today().isoformat()
    page.write_text(ecrire_etat(html, etat), encoding="utf-8")
    print(f"  ✓ {x['id']} → {x['statut']} : {x['titre']}")
    return 0


def _projet_existant(etat: dict, pid: str) -> dict:
    p = projet_de(etat, pid)
    if p is None:
        raise SystemExit(f"✗ projet {pid} absent du tableau de bord")
    return p


def cmd_mois_cible(a) -> int:
    """Programme une action dans un mois de la roadmap (ou la rend à son mois d'origine avec --retirer)."""
    if not a.mois and not a.retirer:
        raise SystemExit("✗ --mois AAAA-MM ou --retirer")
    page = Path(a.html)
    html = page.read_text(encoding="utf-8")
    etat = lire_etat(html)
    x = programmer_action(_projet_existant(etat, a.projet_id), a.id, None if a.retirer else a.mois)
    etat["maj"] = dt.date.today().isoformat()
    page.write_text(ecrire_etat(html, etat), encoding="utf-8")
    ou = x.get("mois_cible") or f"mois d'origine ({x.get('mois', '?')})"
    print(f"  ✓ {x['id']} → {ou} : {x['titre']}")
    return 0


def cmd_lien(a) -> int:
    """Consigne un lien obtenu (reporting mensuel du netlinking) dans la vue Backlinks."""
    page = Path(a.html)
    html = page.read_text(encoding="utf-8")
    etat = lire_etat(html)
    p = projet_de(etat, a.projet_id, creer=True)
    lien = {"date": a.date or "", "domaine": (a.domaine or "").strip().lower(), "url": a.url, "cible": a.cible or "",
            "ancre": a.ancre or "", "prix": prix_de(a.prix), "attribut": (a.attribut or "").strip().lower(),
            "statut": a.statut or "", "note": a.note or ""}
    x, neuf = ajouter_lien(p, lien)
    etat["maj"] = dt.date.today().isoformat()
    page.write_text(ecrire_etat(html, etat), encoding="utf-8")
    print(f"  ✓ lien {'ajouté' if neuf else 'mis à jour'} : {x['domaine']} → {x.get('cible', '')} "
          f"({len(p['liens'])} lien(s) consigné(s))")
    return 0


def fusionner_mois(p: dict, bilan: dict) -> dict:
    """Reporte un bilan dans l'onglet de son mois, sans perdre ce qui y est déjà.

    `bilan` : {"mois": "AAAA-MM", "synthese", "reporting": {…}, "wins": [{texte, lien}],
    "contenus": [{titre, url, statut, notion, date}], "semaine": {"date", "resume", …}}.
    Un win ou un contenu déjà présent (même texte, même URL) est mis à jour, pas dupliqué ;
    une semaine déjà écrite (même date) est remplacée : relancer la routine ne double rien."""
    cle = bilan.get("mois") or dt.date.today().strftime("%Y-%m")
    m = p.setdefault("mois", {}).setdefault(cle, {})
    for champ in ("synthese",):
        if bilan.get(champ):
            m[champ] = bilan[champ]
    if bilan.get("reporting"):
        m.setdefault("reporting", {}).update(bilan["reporting"])
    for champ, ident in (("wins", "texte"), ("contenus", "url")):
        liste = m.setdefault(champ, [])
        for el in bilan.get(champ) or []:
            k = (el.get(ident) or el.get("titre") or "").strip().lower()
            existant = next((x for x in liste if (x.get(ident) or x.get("titre") or "").strip().lower() == k), None)
            if existant:
                existant.update({c: v for c, v in el.items() if v})
            else:
                liste.append(el)
    if bilan.get("semaine"):
        semaines = [s for s in m.setdefault("semaines", []) if s.get("date") != bilan["semaine"].get("date")]
        m["semaines"] = sorted(semaines + [bilan["semaine"]], key=lambda s: s.get("date", ""))
    return m


def _fusionner_liste(liste: list[dict], nouveaux: list[dict], ident: str) -> list[dict]:
    """Ajoute ou met à jour des éléments repérés par `ident` (casse et espaces ignorés) : jamais de doublon."""
    for el in nouveaux or []:
        k = str(el.get(ident) or "").strip().lower()
        existant = next((x for x in liste if k and str(x.get(ident) or "").strip().lower() == k), None)
        if existant:
            existant.update({c: v for c, v in el.items() if v not in (None, "")})
        else:
            liste.append(el)
    return liste


# Clé d'identification des listes du plan de netlinking (vue Backlinks).
IDENT_BACKLINKS = {"indicateurs": "nom", "pages": "page", "regles": "titre", "documents": "url", "guide": "titre"}
IDENT_MOIS_BACKLINKS = {"taches": "texte", "cibles": "nom"}
# Blocs d'une section du guide : un seul type par bloc, rendu tel quel (texte brut, **gras** et adresses http(s) seulement).
TYPES_BLOCS_GUIDE = ("texte", "liste", "cases", "table", "copie", "note")


def _cle(v) -> str:
    return str(v or "").strip().lower()


def _retirer(conteneur: dict, consignes: list, idents: dict) -> list[str]:
    """Retire ce que le plan désigne : une clé entière ("brief") ou un élément d'une liste ({"documents": "<url>"}).

    Seul moyen de faire disparaître un élément : la fusion, elle, ne supprime jamais rien."""
    faits = []
    for c in consignes or []:
        if isinstance(c, str):
            if conteneur.pop(c, None) is not None:
                faits.append(c)
            continue
        for liste, valeur in (c or {}).items():
            if liste not in idents:
                raise SystemExit(f"✗ retirer : liste inconnue « {liste} » (attendu : {', '.join(idents)})")
            avant = conteneur.get(liste) or []
            conteneur[liste] = [x for x in avant if _cle(x.get(idents[liste])) != _cle(valeur)]
            if len(conteneur[liste]) < len(avant):
                faits.append(f"{liste} : {valeur}")
    return faits


def _verifier_guide(sections: list) -> None:
    for s in sections or []:
        if not str(s.get("titre") or "").strip():
            raise SystemExit("✗ guide : chaque section a un titre")
        for bloc in s.get("blocs") or []:
            types = [t for t in TYPES_BLOCS_GUIDE if t in bloc]
            if len(types) != 1:
                raise SystemExit(f"✗ guide « {s['titre']} » : un bloc porte un seul type parmi {', '.join(TYPES_BLOCS_GUIDE)}")
            if "table" in bloc and not isinstance(bloc["table"], dict):
                raise SystemExit(f"✗ guide « {s['titre']} » : table = {{colonnes, lignes}}")


def fusionner_backlinks(p: dict, plan: dict) -> dict:
    """Reporte un plan de netlinking dans la vue Backlinks, mois par mois, sans rien perdre.

    `plan` : {"synthese", "responsable", "brief": {titre, url}, "documents": [{titre, url, note}],
    "indicateurs": [{nom, depart, cible_3m, cible_6m, mesure}], "pages": [{page, requete, depart, liens, note}],
    "regles": [{titre, texte}], "guide": [{titre, intro, blocs: [{titre?, texte | liste (+ordonnee) | cases |
    table: {colonnes, lignes} | copie | note}]}], "retirer": ["brief", {"documents": "<url>"}],
    "mois": {"AAAA-MM": {titre, objectif, cible, budget, temps, note, "retirer": [{"taches": "<texte>"}],
    "taches": [{qui, texte, statut, action, lien}], "cibles": [{nom, priorite, type, etat, cout, lien, url}]}}}.
    Un élément déjà présent (même nom, même texte, même page, même titre de section) est mis à jour ; relancer
    ne double rien. `retirer` passe avant la fusion. Le guide rend la vue autonome (le consultant n'a besoin
    d'aucun autre document) : textes, listes, cases à cocher, tableaux, blocs à copier (bouton « Copier »).
    Une tâche reliée à une action (`action` = id) prend dans la page le statut de cette action."""
    for m in plan.get("mois") or {}:
        mois_valide(m)
    _verifier_guide(plan.get("guide"))
    b = p.setdefault("backlinks", {})
    _retirer(b, plan.get("retirer"), IDENT_BACKLINKS)
    for m, contenu in (plan.get("mois") or {}).items():
        if contenu.get("retirer") and m in (b.get("mois") or {}):
            _retirer(b["mois"][m], contenu["retirer"], IDENT_MOIS_BACKLINKS)
    for cle, v in plan.items():
        if cle in ("mois", "retirer") or v in (None, "", [], {}):
            continue
        if cle in IDENT_BACKLINKS:
            b[cle] = _fusionner_liste(b.setdefault(cle, []), v, IDENT_BACKLINKS[cle])
        else:
            b[cle] = v
    for m, contenu in (plan.get("mois") or {}).items():
        if not set(contenu) - {"retirer"}:
            continue
        cible = b.setdefault("mois", {}).setdefault(m, {})
        for cle, v in contenu.items():
            if cle == "retirer" or v in (None, "", [], {}):
                continue
            if cle in IDENT_MOIS_BACKLINKS:
                cible[cle] = _fusionner_liste(cible.setdefault(cle, []), v, IDENT_MOIS_BACKLINKS[cle])
            else:
                cible[cle] = v
    if b.get("mois"):
        b["mois"] = dict(sorted(b["mois"].items()))
    return b


def fusionner_programme(p: dict, prog: dict) -> dict:
    """En-tête et phases du programme (frise de la roadmap) : {surtitre, intro, debut, fin, phases: [{titre, debut, fin, texte}]}.

    Les phases sont repérées par leur titre ; une phase reprise est mise à jour, jamais doublée."""
    for cle in ("debut", "fin"):
        if prog.get(cle):
            mois_valide(prog[cle])
    for ph in prog.get("phases") or []:
        for cle in ("debut", "fin"):
            mois_valide(ph.get(cle) or "")
    g = p.setdefault("programme", {})
    for cle, v in prog.items():
        if v in (None, "", []):
            continue
        g[cle] = _fusionner_liste(g.setdefault("phases", []), v, "titre") if cle == "phases" else v
    if g.get("phases"):
        g["phases"].sort(key=lambda x: (x.get("debut", ""), x.get("fin", "")))
    return g


def _commande_fichier(a, fusion, libelle: str) -> int:
    page = Path(a.html)
    html = page.read_text(encoding="utf-8")
    etat = lire_etat(html)
    p = projet_de(etat, a.projet_id, creer=True)
    r = fusion(p, json.loads(Path(a.fichier).read_text(encoding="utf-8")))
    etat["maj"] = dt.date.today().isoformat()
    page.write_text(ecrire_etat(html, etat), encoding="utf-8")
    print(f"  ✓ {libelle} · " + ", ".join(f"{k} : {len(v)}" for k, v in r.items() if isinstance(v, (list, dict))))
    return 0


def cmd_backlinks(a) -> int:
    return _commande_fichier(a, fusionner_backlinks, "plan de netlinking (vue Backlinks)")


def cmd_programme(a) -> int:
    return _commande_fichier(a, fusionner_programme, "programme (en-tête et phases)")


def cmd_mois(a) -> int:
    page = Path(a.html)
    html = page.read_text(encoding="utf-8")
    etat = lire_etat(html)
    p = projet_de(etat, a.projet_id, creer=True)
    bilan = json.loads(Path(a.fichier).read_text(encoding="utf-8"))
    m = fusionner_mois(p, bilan)
    etat["maj"] = dt.date.today().isoformat()
    page.write_text(ecrire_etat(html, etat), encoding="utf-8")
    print(f"  ✓ onglet {bilan.get('mois') or 'du mois'} · {len(m.get('semaines', []))} semaine(s), "
          f"{len(m.get('wins', []))} win(s), {len(m.get('contenus', []))} contenu(s)")
    return 0


def cmd_sauvegarder(a) -> int:
    """Copie de sûreté du projet dans git : la page publiée n'est pas la seule à garder la roadmap.

    Seule la part de ce projet est écrite (la page peut porter d'autres projets)."""
    p = projet_de(lire_etat(Path(a.html).read_text(encoding="utf-8")), a.projet_id)
    if p is None:
        raise SystemExit(f"✗ projet {a.projet_id} absent du tableau de bord")
    sortie = Path(a.sortie)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(json.dumps(p, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"  ✓ {sortie} · {len(p.get('actions', []))} action(s), {len(p.get('mois', {}))} mois, "
          f"{len(p.get('liens', []))} lien(s)")
    return 0


def cmd_restaurer(a) -> int:
    """Remet dans la page la part d'un projet depuis sa copie git (page abîmée, ou nouvelle page)."""
    page = Path(a.html)
    html = page.read_text(encoding="utf-8")
    etat = lire_etat(html)
    copie = json.loads(Path(a.depuis).read_text(encoding="utf-8"))
    if copie.get("id") != a.projet_id:
        raise SystemExit(f"✗ la copie est celle du projet {copie.get('id')}, pas {a.projet_id}")
    etat["projets"] = [x for x in etat.get("projets", []) if x.get("id") != a.projet_id] + [copie]
    etat["maj"] = dt.date.today().isoformat()
    page.write_text(ecrire_etat(html, etat), encoding="utf-8")
    print(f"  ✓ {page} · projet {a.projet_id} restauré ({len(copie.get('actions', []))} action(s))")
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
    p.add_argument("--titre", help="nom de la page (ex. « Pilotage Atlas Conseil »)")
    p.add_argument("--livrables", help="JSON [{titre, url, note}] : pages de travail et comptes rendus liés")
    p.add_argument("--theme", help="JSON de la charte du projet : {mode: sombre|clair, fond, carte, encre, doux, trait, "
                                   "accent, accent_doux, cta, cta_texte, lien, titre, texte, polices (URL Google Fonts)}")
    p.set_defaults(f=cmd_injecter)
    p = sp.add_parser("integrer", help="loger le tableau de bord dans une page existante (Artifact déjà en place)")
    p.add_argument("--hote", required=True, help="HTML de la page existante (lue avec l'outil Artifact)")
    p.add_argument("--etat-depuis", help="page de suivi dont on reprend l'état (roadmap, chiffres)")
    p.add_argument("--titre", help="par défaut, le titre de la page existante")
    p.add_argument("--sortie", required=True)
    p.set_defaults(f=cmd_integrer)
    p = sp.add_parser("ajouter", help="consigner une action faite ou décidée dans une conversation")
    p.add_argument("--html", required=True)
    p.add_argument("--projet-id", required=True)
    p.add_argument("--titre", required=True)
    p.add_argument("--type", default="optimisation", choices=["decision", "optimisation", "contenu", "technique"])
    p.add_argument("--statut", default="faite", choices=STATUTS)
    p.add_argument("--chantier", choices=CHANTIERS, help="rangement dans la page (défaut : déduit du type)")
    p.add_argument("--page")
    p.add_argument("--pourquoi")
    p.add_argument("--gain")
    p.add_argument("--effort", default="M")
    p.add_argument("--lien")
    p.add_argument("--note")
    p.add_argument("--attend", help="action bloquée : qui ou quoi on attend")
    p.add_argument("--qui", help="qui porte l'action (Claude, Nathan, consultant…) ; défaut : déduit du statut et d'--attend")
    p.add_argument("--mois-cible", help="AAAA-MM : mois de la roadmap où l'action est programmée")
    p.add_argument("--date", help="AAAA-MM-JJ : date de l'action (défaut : aujourd'hui), pour reprendre un historique")
    p.set_defaults(f=cmd_ajouter)
    p = sp.add_parser("etat", help="actions d'un projet")
    p.add_argument("--html", required=True)
    p.add_argument("--projet-id", required=True)
    p.add_argument("--statut", choices=STATUTS)
    p.add_argument("--toutes", action="store_true",
                   help="avec --statut : lister aussi les actions programmées après le mois en cours (mois_cible)")
    p.add_argument("--json", action="store_true")
    p.set_defaults(f=cmd_etat)
    p = sp.add_parser("marquer", help="changer le statut d'une action")
    p.add_argument("--html", required=True)
    p.add_argument("--projet-id", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--statut", required=True, choices=STATUTS)
    p.add_argument("--lien")
    p.add_argument("--note")
    p.add_argument("--attend", help="avec --statut bloquee : qui ou quoi on attend")
    p.set_defaults(f=cmd_marquer)
    p = sp.add_parser("mois-cible", help="programmer une action dans un mois de la roadmap")
    p.add_argument("--html", required=True)
    p.add_argument("--projet-id", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--mois", help="AAAA-MM")
    p.add_argument("--retirer", action="store_true", help="rendre l'action à son mois d'origine")
    p.set_defaults(f=cmd_mois_cible)
    p = sp.add_parser("lien", help="consigner un lien obtenu (vue Backlinks, reporting du netlinking)")
    p.add_argument("--html", required=True)
    p.add_argument("--projet-id", required=True)
    p.add_argument("--url", required=True, help="URL de la page qui fait le lien")
    p.add_argument("--domaine", help="défaut : le domaine de --url")
    p.add_argument("--cible", help="page du site qui reçoit le lien (ex. /audit-geo/)")
    p.add_argument("--ancre")
    p.add_argument("--prix", help="en euros (ex. 180 ou 180,50) ; vide pour un lien gratuit")
    p.add_argument("--attribut", help="dofollow, nofollow, sponsored, ugc")
    p.add_argument("--statut", default="en-ligne", help="en-ligne, commandé, à relancer, perdu… (défaut : en-ligne)")
    p.add_argument("--date", help="AAAA-MM-JJ : date de mise en ligne (défaut : aujourd'hui)")
    p.add_argument("--note")
    p.set_defaults(f=cmd_lien)
    p = sp.add_parser("mois", help="reporter le bilan de la semaine (ou du mois) dans l'onglet du mois")
    p.add_argument("--html", required=True)
    p.add_argument("--projet-id", required=True)
    p.add_argument("--fichier", required=True, help="JSON {mois, synthese, reporting, wins, contenus, semaine}")
    p.set_defaults(f=cmd_mois)
    p = sp.add_parser("backlinks", help="plan de netlinking mois par mois (vue Backlinks) : objectifs, tâches, cibles")
    p.add_argument("--html", required=True)
    p.add_argument("--projet-id", required=True)
    p.add_argument("--fichier", required=True,
                   help="JSON {synthese, responsable, brief, documents, indicateurs, pages, regles, guide, retirer, "
                        "mois: {AAAA-MM: {…}}}")
    p.set_defaults(f=cmd_backlinks)
    p = sp.add_parser("programme", help="en-tête du programme et phases de la roadmap (frise)")
    p.add_argument("--html", required=True)
    p.add_argument("--projet-id", required=True)
    p.add_argument("--fichier", required=True, help="JSON {surtitre, intro, debut, fin, phases: [{titre, debut, fin, texte}]}")
    p.set_defaults(f=cmd_programme)
    p = sp.add_parser("sauvegarder", help="copie de sûreté du projet dans git")
    p.add_argument("--html", required=True)
    p.add_argument("--projet-id", required=True)
    p.add_argument("--sortie", default=SAUVEGARDE)
    p.set_defaults(f=cmd_sauvegarder)
    p = sp.add_parser("restaurer", help="remettre un projet dans la page depuis sa copie git")
    p.add_argument("--html", required=True)
    p.add_argument("--projet-id", required=True)
    p.add_argument("--depuis", default=SAUVEGARDE)
    p.set_defaults(f=cmd_restaurer)
    a = ap.parse_args()
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
