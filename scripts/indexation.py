#!/usr/bin/env python3
"""Faire indexer les pages publiées, proprement, depuis le dépôt du projet.

    python3 indexation.py cle                          # crée une clé IndexNow et dit où la publier
    python3 indexation.py annoncer https://www.exemple.com/page-neuve/ [autres URL]
    python3 indexation.py annoncer --fichier urls.txt
    python3 indexation.py suivre                       # J+3 : indexée ou pas, et la liste du jour
    python3 indexation.py auto                         # sitemap → annonce les pages publiées ou modifiées
    python3 indexation.py auto --jours 2 --sans-registre   # version GitHub Actions (chaque jour)

C'est l'équivalent de l'« indexation instantanée » des extensions WordPress,
sans ce qui est hors des règles :

- `annoncer` envoie les URL à IndexNow (Bing, Yandex, Seznam, Naver, Yep,
  Amazon ; Bing alimente Copilot), resoumet les sitemaps à Google par l'API
  Search Console, et inscrit chaque URL dans donnees/indexation.csv ;
- `suivre` inspecte, par l'API URL Inspection (lecture seule, 2 000/jour),
  les URL annoncées depuis au moins 3 jours, met le registre à jour, sort
  les 10 URL à passer à la main dans Search Console (« Demander l'indexation »)
  et inscrit le constat dans rapports/a-valider.md : le script propose, un
  humain décide (enrichir, mailler, sortir du sitemap, restaurer une 404) ;
- `auto` lit le sitemap du site et annonce les URL dont la date de
  modification (`lastmod`) est récente : c'est l'automatisme quotidien
  (`.github/workflows/indexation.yml` du gabarit), sans état à commiter.

Ce que le script ne fait pas, volontairement : appeler l'Indexing API de
Google. Elle est réservée aux offres d'emploi (JobPosting) et aux vidéos en
direct (BroadcastEvent) ; Google a écrit en 2024 que les abus peuvent couper
l'accès. Il n'automatise pas non plus l'interface de Search Console.

Variables : INDEXNOW_KEY (clé publiée à la racine du site), GSC_SA_JSON et
GSC_SITE_URL (voir gsc.py). Chaque brique manquante est signalée, jamais
bloquante pour les autres.
"""

from __future__ import annotations

import argparse
import re
import csv
import datetime as dt
import json
import os
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsc  # noqa: E402
from _projet import lire_valeur, racine_projet  # noqa: E402

REGISTRE_REL = Path("donnees") / "indexation.csv"
CHAMPS = ["url", "annoncee_le", "indexnow", "statut", "verifiee_le", "detail"]
DELAI_JOURS = 3
LISTE_DU_JOUR = 10
AGENT = "decupler-seo-indexation/1.0"
A_VALIDER_REL = Path("rapports") / "a-valider.md"
DEBUT_SECTION = "<!-- indexation:debut -->"
FIN_SECTION = "<!-- indexation:fin -->"
SITEMAPS_CANDIDATS = ("sitemap_index.xml", "sitemap.xml", "wp-sitemap.xml")

# Ce que veut dire chaque état de Search Console, et ce qu'on propose (jamais fait seul).
DIAGNOSTICS = [
    ("introuvable", "URL en erreur (404 ou 410) dans le sitemap",
     "restaurer la page si elle doit vivre, sinon la retirer du sitemap (et 410 si elle a été piratée)"),
    ("explorée", "Google l'a lue et ne l'a pas gardée : jugement de valeur sur le contenu",
     "enrichir avec ce que le top 10 n'a pas, ou fusionner avec une page proche (301)"),
    ("détectée", "Google la connaît sans l'explorer : qualité perçue ou budget d'exploration",
     "liens internes depuis des pages qui rankent, réduire les pages faibles du même gabarit"),
    ("ne reconnaît pas", "Google ne connaît pas l'URL",
     "un lien interne depuis l'accueil ou une page hub, vérifier qu'elle est dans le sitemap déclaré"),
    ("bloquée", "bloquée par robots.txt ou exclue par noindex",
     "vérifier que c'est voulu ; sinon corriger la directive (niveau Interdit : proposition seulement)"),
]


def registre_csv() -> Path:
    return racine_projet() / REGISTRE_REL


def lire_registre() -> list[dict]:
    REGISTRE = registre_csv()
    if not REGISTRE.is_file():
        return []
    with open(REGISTRE, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def ecrire_registre(lignes: list[dict]) -> None:
    REGISTRE = registre_csv()
    REGISTRE.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CHAMPS)
        w.writeheader()
        for ligne in lignes:
            w.writerow({k: ligne.get(k, "") for k in CHAMPS})


def http(url: str, donnees: bytes | None = None) -> tuple[int, str]:
    entetes = {"User-Agent": AGENT}
    if donnees is not None:
        entetes["Content-Type"] = "application/json; charset=utf-8"
    requete = urllib.request.Request(url, data=donnees, headers=entetes, method="POST" if donnees else "GET")
    try:
        with urllib.request.urlopen(requete, timeout=60) as rep:
            return rep.status, rep.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, ""
    except (urllib.error.URLError, OSError) as exc:
        return 0, str(exc)


def indexnow(urls: list[str]) -> str:
    """Soumet les URL d'un même site à IndexNow. Renvoie un statut lisible."""
    cle = os.environ.get("INDEXNOW_KEY", "").strip()
    if not cle:
        return "sans clé (INDEXNOW_KEY absente)"
    hotes = {urllib.parse.urlparse(u).netloc for u in urls}
    if len(hotes) != 1:
        return "refusé : une annonce = un seul site"
    hote = hotes.pop()
    racine = f"https://{hote}"
    code, contenu = http(f"{racine}/{cle}.txt")
    if code != 200 or contenu.strip() != cle:
        return f"refusé : {racine}/{cle}.txt absent ou différent de la clé"
    corps = json.dumps({"host": hote, "key": cle, "keyLocation": f"{racine}/{cle}.txt",
                        "urlList": urls[:10000]}).encode()
    code, _ = http("https://api.indexnow.org/indexnow", corps)
    return {200: "ok", 202: "ok (en attente de validation de la clé)"}.get(code, f"erreur HTTP {code}")


def resoumettre_sitemaps() -> str:
    try:
        site = gsc.site_par_defaut()
        base = f"{gsc.API}/sites/{urllib.parse.quote(site, safe='')}/sitemaps"
        chemins = [sm["path"] for sm in gsc.appel(base).get("sitemap", [])]
        for chemin in chemins:
            gsc.appel(f"{base}/{urllib.parse.quote(chemin, safe='')}", methode="PUT", ecriture=True)
        return f"{len(chemins)} sitemap(s) resoumis" if chemins else "aucun sitemap déclaré dans Search Console"
    except (gsc.ErreurGSC, SystemExit, KeyError) as exc:
        return f"non fait ({str(exc).strip() or 'Search Console non branchée'})"


def cmd_cle(_a) -> int:
    cle = secrets.token_hex(16)
    print(f"\n  Clé IndexNow : {cle}\n")
    print(f"  1. Publiez un fichier texte {cle}.txt à la racine du site, qui contient seulement la clé.")
    print("     WordPress : Rank Math (module Instant Indexing) ou Yoast le font pour vous ;")
    print("     site en code : ajoutez le fichier au dossier public.")
    print("  2. Ajoutez INDEXNOW_KEY à l'environnement (jamais dans le dépôt).\n")
    return 0


def cmd_annoncer(a) -> int:
    urls = list(a.url or [])
    if a.fichier:
        urls += [u.strip() for u in open(a.fichier, encoding="utf-8") if u.strip()]
    urls = list(dict.fromkeys(u for u in urls if u.startswith("http")))
    if not urls:
        print("✗ Aucune URL à annoncer.")
        return 1
    statut_indexnow = indexnow(urls)
    statut_sitemaps = resoumettre_sitemaps()
    aujourd_hui = dt.date.today().isoformat()
    registre = {l["url"]: l for l in lire_registre()}
    for u in urls:
        registre[u] = {"url": u, "annoncee_le": aujourd_hui, "indexnow": statut_indexnow,
                       "statut": "en attente", "verifiee_le": "", "detail": ""}
    ecrire_registre(list(registre.values()))
    print(f"\n  {len(urls)} URL annoncée(s)")
    print(f"  IndexNow  : {statut_indexnow}")
    print(f"  Sitemaps  : {statut_sitemaps}")
    print(f"  Registre  : {REGISTRE_REL} · vérification par `indexation.py suivre` à partir de J+{DELAI_JOURS}\n")
    return 0


def cmd_suivre(a) -> int:
    lignes = lire_registre()
    limite = dt.date.today() - dt.timedelta(days=a.delai)
    a_verifier = [l for l in lignes if l["statut"] != "indexée" and l["annoncee_le"] <= limite.isoformat()]
    if not a_verifier:
        print(f"\n  Rien à vérifier : aucune URL non indexée annoncée depuis {a.delai} jours ou plus.\n")
        return 0
    try:
        site = gsc.site_par_defaut()
        for l in a_verifier:
            r = gsc.appel(gsc.INSPECT, {"inspectionUrl": l["url"], "siteUrl": site, "languageCode": "fr"}) \
                .get("inspectionResult", {}).get("indexStatusResult", {})
            l["statut"] = "indexée" if r.get("verdict") == "PASS" else "non indexée"
            l["detail"] = r.get("coverageState", "")
            l["verifiee_le"] = dt.date.today().isoformat()
    except (gsc.ErreurGSC, SystemExit) as exc:
        print(f"\n  ✗ Inspection impossible : {str(exc).strip() or 'Search Console non branchée'}")
        print("    Branchez GSC_SA_JSON et GSC_SITE_URL (voir gsc.py), puis relancez.\n")
        return 2
    ecrire_registre(lignes)
    restantes = sorted((l for l in a_verifier if l["statut"] != "indexée"), key=lambda l: l["annoncee_le"])
    print(f"\n  {len(a_verifier) - len(restantes)} indexée(s) · {len(restantes)} non indexée(s)\n")
    if restantes:
        print(f"  À passer à la main aujourd'hui (Search Console → Inspection de l'URL → Demander "
              f"l'indexation), {LISTE_DU_JOUR} au plus :")
        for l in restantes[:LISTE_DU_JOUR]:
            print(f"    {l['url']}  · annoncée le {l['annoncee_le']} · {l['detail']}")
        print("\n  Avant de demander : la page est-elle liée depuis l'accueil ou une page hub ? "
              "Une page orpheline revient vite dans cette liste.\n")
    if not a.sans_rapport:
        chemin = remonter_constat(restantes)
        print(f"  Constat inscrit dans {chemin} : à décider par un humain.\n")
    return 0


def diagnostic(detail: str) -> tuple[str, str]:
    bas = detail.lower()
    for cle, sens, proposition in DIAGNOSTICS:
        if cle in bas:
            return sens, proposition
    return "état non classé", "inspecter l'URL dans Search Console"


def remonter_constat(restantes: list[dict]) -> Path:
    """Écrit (ou remplace) la section indexation de rapports/a-valider.md.

    Le script ne décide rien : il regroupe les URL non indexées par cause
    et propose une action par groupe, pour qu'un humain tranche.
    """
    chemin = racine_projet() / A_VALIDER_REL
    chemin.parent.mkdir(parents=True, exist_ok=True)
    texte = chemin.read_text(encoding="utf-8") if chemin.is_file() else "# À valider\n"
    groupes: dict[tuple[str, str], list[dict]] = {}
    for l in restantes:
        groupes.setdefault(diagnostic(l.get("detail", "")), []).append(l)
    jour = dt.date.today().isoformat()
    lignes = [DEBUT_SECTION, f"## Indexation — constat du {jour} (`indexation.py suivre`)", ""]
    if not restantes:
        lignes.append("Toutes les URL annoncées sont indexées. Rien à décider.")
    for (sens, proposition), lot in sorted(groupes.items(), key=lambda g: -len(g[1])):
        lignes.append(f"- [ ] **{len(lot)} URL : {sens}.** Proposition : {proposition}.")
        for l in lot[:15]:
            lignes.append(f"  - {l['url']} (annoncée le {l['annoncee_le']}, {l.get('detail') or 'état inconnu'})")
        if len(lot) > 15:
            lignes.append(f"  - … et {len(lot) - 15} autres : `donnees/indexation.csv`")
    lignes += ["", "Redemander l'indexation de ces pages ne règle rien tant que la cause reste : "
               "on traite la cause, puis on annonce à nouveau.", FIN_SECTION]
    section = "\n".join(lignes)
    if DEBUT_SECTION in texte and FIN_SECTION in texte:
        avant, _, reste = texte.partition(DEBUT_SECTION)
        _, _, apres = reste.partition(FIN_SECTION)
        texte = avant + section + apres
    else:
        texte = texte.rstrip("\n") + "\n\n" + section + "\n"
    chemin.write_text(texte, encoding="utf-8")
    return A_VALIDER_REL


def site_public() -> str:
    domaine = os.environ.get("SEO_SITE_URL", "").strip() or lire_valeur("projet.domaine")
    if not domaine:
        raise SystemExit("✗ Domaine inconnu : renseignez projet.domaine dans decupler-seo.config.yml "
                         "ou la variable SEO_SITE_URL.")
    return domaine.rstrip("/")


def urls_du_sitemap(racine: str) -> list[tuple[str, str]]:
    """(URL, lastmod) de toutes les URL du sitemap, index de sitemaps compris."""
    code, robots = http(f"{racine}/robots.txt")
    departs = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", robots) if code == 200 else []
    if not departs:
        for nom in SITEMAPS_CANDIDATS:
            if http(f"{racine}/{nom}")[0] == 200:
                departs = [f"{racine}/{nom}"]
                break
    vues, resultat, a_lire = set(), [], list(departs)
    while a_lire:
        url = a_lire.pop(0)
        if url in vues:
            continue
        vues.add(url)
        code, xml = http(url)
        if code != 200:
            continue
        blocs = re.findall(r"<(sitemap|url)>(.*?)</\1>", xml, re.S)
        for nature, bloc in blocs:
            loc = re.search(r"<loc>\s*([^<\s]+)\s*</loc>", bloc)
            mod = re.search(r"<lastmod>\s*([^<\s]+)\s*</lastmod>", bloc)
            if not loc:
                continue
            if nature == "sitemap":
                a_lire.append(loc.group(1))
            else:
                resultat.append((loc.group(1), mod.group(1)[:10] if mod else ""))
    return list(dict.fromkeys(resultat))


def cmd_auto(a) -> int:
    racine = site_public()
    urls = urls_du_sitemap(racine)
    if not urls:
        print(f"✗ Aucun sitemap lisible pour {racine} (robots.txt, /sitemap_index.xml, /sitemap.xml).")
        return 1
    seuil = (dt.date.today() - dt.timedelta(days=a.jours)).isoformat()
    recentes = [u for u, mod in urls if mod and mod >= seuil]
    sans_date = sum(1 for _, mod in urls if not mod)
    print(f"\n  {racine} · {len(urls)} URL dans le sitemap · {len(recentes)} modifiée(s) depuis {seuil}")
    if sans_date:
        print(f"  ! {sans_date} URL sans lastmod : le sitemap devrait dater chaque page")
    if not recentes:
        print("  Rien de neuf à annoncer.\n")
        return 0
    if a.sans_registre:
        print(f"  IndexNow  : {indexnow(recentes)}")
        print(f"  Sitemaps  : {resoumettre_sitemaps()}\n")
        return 0
    return cmd_annoncer(argparse.Namespace(url=recentes, fichier=None))


def main() -> int:
    gsc.charger_env()
    ap = argparse.ArgumentParser(description="Annoncer et suivre l'indexation des pages publiées")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("cle", help="créer une clé IndexNow").set_defaults(f=cmd_cle)
    p = sub.add_parser("annoncer", help="IndexNow + sitemaps + registre, après publication")
    p.add_argument("url", nargs="*")
    p.add_argument("--fichier", help="une URL par ligne")
    p.set_defaults(f=cmd_annoncer)
    p = sub.add_parser("suivre", help="inspecter les URL annoncées et sortir la liste du jour")
    p.add_argument("--delai", type=int, default=DELAI_JOURS, help="jours d'attente avant inspection")
    p.add_argument("--sans-rapport", action="store_true", help="ne pas écrire dans rapports/a-valider.md")
    p.set_defaults(f=cmd_suivre)
    p = sub.add_parser("auto", help="annoncer les URL du sitemap modifiées récemment (lastmod)")
    p.add_argument("--jours", type=int, default=7, help="fenêtre de modification, en jours")
    p.add_argument("--sans-registre", action="store_true",
                   help="ne rien écrire dans le dépôt (GitHub Actions)")
    p.set_defaults(f=cmd_auto)
    a = ap.parse_args()
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
