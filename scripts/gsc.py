#!/usr/bin/env python3
"""Google Search Console en direct, sans intermédiaire.

    python3 gsc.py sites
    python3 gsc.py perf --par page --lignes 40 --compare
    python3 gsc.py page --url https://exemple.com/page            # 28 derniers jours, en JSON
    python3 gsc.py instantane                                     # → donnees/AAAA-SWW.json
    python3 gsc.py temoin --avant-fin 2026-09-01 --apres-fin 2026-09-29 --exclure urls.txt
    python3 gsc.py inspect --url https://exemple.com/page
    python3 gsc.py sitemap [--resoumettre]

La propriété vient de --site, sinon de GSC_SITE_URL, sinon du domaine de la
config du projet. Format « sc-domain:exemple.com » accepté.

Authentification, la première trouvée gagne :

  1. Compte de service — GSC_SA_JSON (le contenu du fichier de clé, JSON ou
     base64) ou GSC_CREDENTIALS_JSON (le chemin du fichier). Voie recommandée :
     pas d'écran de consentement, pas de jeton qui expire. L'adresse
     client_email doit être ajoutée comme utilisateur dans Search Console,
     propriété par propriété, en lecture seule.
  2. OAuth utilisateur — GSC_CLIENT_ID, GSC_CLIENT_SECRET, GSC_REFRESH_TOKEN.

Aucune dépendance : la signature RS256 du compte de service est faite en
Python pur (voir _signer_rs256_pur).

Utilisable aussi comme module : journal.py appelle mesures_page() et
variation_temoin() pour relever lui-même les chiffres avant et après.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import charger_env, lire_valeur, racine_projet, resoudre  # noqa: E402

API = "https://www.googleapis.com/webmasters/v3"
INSPECT = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"
LATENCE_JOURS = 3          # Search Console accuse 2 à 3 jours de retard
LIGNES_MAX = 25000         # plafond d'une requête Search Analytics


class ErreurGSC(RuntimeError):
    """Levée plutôt qu'un sys.exit, pour que journal.py puisse la rattraper."""


# ─── Authentification ─────────────────────────────────────────────

def _env(cle: str) -> str:
    import os
    return os.environ.get(cle, "").strip()


def _b64(donnees: bytes) -> str:
    return base64.urlsafe_b64encode(donnees).decode().rstrip("=")


def lis_cle(brut: str) -> dict:
    """Accepte le JSON tel quel, ou sa version base64.

    Le fichier de clé contient des retours à la ligne, y compris dans la clé
    privée. Certains formulaires de secrets les avalent, et on se retrouve
    avec une clé illisible sans message clair. Le base64 tient sur une ligne.
    """
    brut = "".join(brut.split())
    if not brut.startswith("{"):
        rembourre = brut + "=" * (-len(brut) % 4)
        for decode in (base64.b64decode, base64.urlsafe_b64decode):
            try:
                brut = decode(rembourre).decode("utf-8")
                break
            except Exception:
                continue
        else:
            raise ErreurGSC("La clé du compte de service n'est ni du JSON ni du base64 lisible.")
    try:
        sa = json.loads(brut)
    except json.JSONDecodeError as exc:
        raise ErreurGSC(f"La clé n'est pas du JSON valide ({exc}). Collez le fichier entier, "
                        "ou sa version base64.") from exc
    manque = [k for k in ("client_email", "private_key") if k not in sa]
    if manque:
        raise ErreurGSC(f"Il manque {', '.join(manque)} : ce n'est pas un fichier de compte de service.")
    return sa


def _cle_compte_de_service() -> dict | None:
    if _env("GSC_SA_JSON"):
        return lis_cle(_env("GSC_SA_JSON"))
    chemin = _env("GSC_CREDENTIALS_JSON")
    if chemin:
        fichier = resoudre(chemin)
        if not fichier.is_file():
            raise ErreurGSC(f"GSC_CREDENTIALS_JSON pointe vers {fichier}, introuvable.")
        return lis_cle(fichier.read_text(encoding="utf-8"))
    return None


def _der(donnees: bytes, pos: int = 0) -> tuple[int, bytes, int]:
    """Lit un élément ASN.1 DER : (étiquette, contenu, position suivante)."""
    etiquette, longueur = donnees[pos], donnees[pos + 1]
    pos += 2
    if longueur & 0x80:
        n = longueur & 0x7F
        longueur = int.from_bytes(donnees[pos:pos + n], "big")
        pos += n
    return etiquette, donnees[pos:pos + longueur], pos + longueur


def _signer_rs256_pur(pem: str, message: bytes) -> bytes:
    """Signature RSA PKCS#1 v1.5 / SHA-256 en Python pur.

    Pourquoi pas `cryptography` : dans certains environnements cloud, le
    paquet système plante au chargement (panique Rust, pas une ImportError),
    et une routine perdrait l'accès à Search Console — donc toute la boucle
    de mesure. Signer un JWT ne demande qu'une exponentiation modulaire ;
    la signature produite est identique octet pour octet à celle d'openssl
    (vérifié par tests/test_gsc.py).
    """
    import hashlib
    corps = "".join(l for l in pem.strip().splitlines() if not l.startswith("-----"))
    der = base64.b64decode(corps)
    _, sequence, _ = _der(der)
    elements, pos = [], 0
    while pos < len(sequence):
        etiquette, contenu, pos = _der(sequence, pos)
        elements.append((etiquette, contenu))
    if len(elements) == 3 and elements[2][0] == 0x04:
        # PKCS#8 : la clé RSA (PKCS#1) est enveloppée dans une OCTET STRING.
        _, sequence, _ = _der(elements[2][1])
        elements, pos = [], 0
        while pos < len(sequence):
            etiquette, contenu, pos = _der(sequence, pos)
            elements.append((etiquette, contenu))
    # RSAPrivateKey : version, n, e, d, p, q, dp, dq, qinv
    n = int.from_bytes(elements[1][1], "big")
    d = int.from_bytes(elements[3][1], "big")
    k = (n.bit_length() + 7) // 8
    info = bytes.fromhex("3031300d060960864801650304020105000420") + hashlib.sha256(message).digest()
    bloc = b"\x00\x01" + b"\xff" * (k - len(info) - 3) + b"\x00" + info
    return pow(int.from_bytes(bloc, "big"), d, n).to_bytes(k, "big")


def _jeton_compte_de_service(sa: dict, scope: str) -> dict:
    """Flux « JWT bearer » : on signe avec la clé privée, Google vérifie avec
    la clé publique qu'il connaît déjà. Pas de navigateur, rien qui expire."""
    maintenant = int(time.time())
    entete = _b64(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    corps = _b64(json.dumps({
        "iss": sa["client_email"], "scope": scope,
        "aud": "https://oauth2.googleapis.com/token",
        "iat": maintenant, "exp": maintenant + 3600}).encode())
    a_signer = f"{entete}.{corps}".encode()
    signature = _b64(_signer_rs256_pur(sa["private_key"], a_signer))

    data = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": f"{entete}.{corps}.{signature}"}).encode()
    with urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=data),
                                timeout=60) as rep:
        return json.load(rep)


_cache: dict = {}


def jeton(ecriture: bool = False) -> str:
    """Lecture seule par défaut. Seule la resoumission de sitemap écrit, et on
    ne prend le scope complet que pour cet appel-là."""
    cle_cache = "ecriture" if ecriture else "lecture"
    valeur, expire = _cache.get(cle_cache, (None, 0))
    if valeur and time.time() < expire - 120:
        return valeur

    scope = ("https://www.googleapis.com/auth/webmasters" if ecriture
             else "https://www.googleapis.com/auth/webmasters.readonly")
    sa = _cle_compte_de_service()
    if sa:
        d = _jeton_compte_de_service(sa, scope)
    elif all(_env(k) for k in ("GSC_CLIENT_ID", "GSC_CLIENT_SECRET", "GSC_REFRESH_TOKEN")):
        data = urllib.parse.urlencode({
            "client_id": _env("GSC_CLIENT_ID"), "client_secret": _env("GSC_CLIENT_SECRET"),
            "refresh_token": _env("GSC_REFRESH_TOKEN"), "grant_type": "refresh_token"}).encode()
        with urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token",
                                                           data=data), timeout=60) as rep:
            d = json.load(rep)
    else:
        raise ErreurGSC("Aucun identifiant Search Console. Définissez GSC_SA_JSON ou "
                        "GSC_CREDENTIALS_JSON (compte de service, recommandé), ou le trio "
                        "GSC_CLIENT_ID / GSC_CLIENT_SECRET / GSC_REFRESH_TOKEN.")

    _cache[cle_cache] = (d["access_token"], time.time() + d.get("expires_in", 3600))
    return d["access_token"]


def identifiants_presents() -> bool:
    return bool(_env("GSC_SA_JSON") or _env("GSC_CREDENTIALS_JSON")
                or all(_env(k) for k in ("GSC_CLIENT_ID", "GSC_CLIENT_SECRET", "GSC_REFRESH_TOKEN")))


def appel(url: str, corps: dict | None = None, methode: str | None = None, ecriture: bool = False):
    requete = urllib.request.Request(
        url, data=json.dumps(corps).encode() if corps is not None else None,
        method=methode or ("POST" if corps is not None else "GET"),
        headers={"Authorization": "Bearer " + jeton(ecriture), "Content-Type": "application/json"})
    for essai in range(5):
        try:
            with urllib.request.urlopen(requete, timeout=120) as rep:
                brut = rep.read()
                return json.loads(brut) if brut else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            # 429 et 5xx se retentent ; une erreur de requête ne se répare pas en la rejouant.
            if exc.code in (429, 500, 502, 503) and essai < 4:
                time.sleep(2 ** essai)
                continue
            if exc.code == 403:
                raise ErreurGSC("HTTP 403. Le compte n'a probablement pas accès à cette propriété : "
                                "Search Console → Paramètres → Utilisateurs et autorisations → "
                                "ajouter l'adresse client_email de la clé, en lecture seule.\n"
                                + detail[:300]) from exc
            raise ErreurGSC(f"HTTP {exc.code} : {detail[:400]}") from exc
        except urllib.error.URLError as exc:
            if essai == 4:
                raise ErreurGSC(f"Search Console injoignable : {exc}") from exc
            time.sleep(2 ** essai)
    raise ErreurGSC("Search Console : échec après 5 tentatives.")


# ─── Propriété et fenêtres ────────────────────────────────────────

def site_par_defaut() -> str:
    if _env("GSC_SITE_URL"):
        return _env("GSC_SITE_URL")
    # Réglage du projet : indispensable quand un même environnement cloud
    # sert plusieurs clients (une seule variable GSC_SITE_URL pour tous).
    propriete = lire_valeur("projet.propriete_gsc")
    if propriete:
        return propriete
    domaine = lire_valeur("projet.domaine")
    if domaine:
        return domaine.rstrip("/") + "/"
    raise ErreurGSC("Propriété inconnue : passez --site, ou définissez GSC_SITE_URL.")


def fenetre(jours: int, fin: dt.date | None = None) -> tuple[str, str]:
    """Fenêtre de `jours` jours se terminant à `fin`, jamais plus récente que la latence."""
    plafond = dt.date.today() - dt.timedelta(days=LATENCE_JOURS)
    fin = min(fin, plafond) if fin else plafond
    return (fin - dt.timedelta(days=jours - 1)).isoformat(), fin.isoformat()


def requete(site: str, dims: list[str], debut: str, fin: str, lignes: int = 1000,
            filtres: list[dict] | None = None) -> list[dict]:
    """Requête Search Analytics, paginée au-delà de 25 000 lignes."""
    resultats, depart = [], 0
    while True:
        corps = {"startDate": debut, "endDate": fin, "dimensions": dims,
                 "rowLimit": min(lignes - len(resultats), LIGNES_MAX), "startRow": depart,
                 "dataState": "final"}
        if filtres:
            corps["dimensionFilterGroups"] = [{"filters": filtres}]
        lot = appel(f"{API}/sites/{urllib.parse.quote(site, safe='')}/searchAnalytics/query",
                    corps).get("rows", [])
        resultats += lot
        if len(lot) < corps["rowLimit"] or len(resultats) >= lignes:
            return resultats
        depart += len(lot)


# ─── Fonctions utilisées par journal.py ───────────────────────────

def mesures_page(url: str, fin: dt.date | None = None, jours: int = 28, site: str | None = None) -> dict:
    """Clics, impressions, CTR (%) et position d'une URL sur `jours` jours."""
    site = site or site_par_defaut()
    debut, fin_txt = fenetre(jours, fin)
    lignes = requete(site, [], debut, fin_txt, 1,
                     [{"dimension": "page", "operator": "equals", "expression": url}])
    r = lignes[0] if lignes else {"clicks": 0, "impressions": 0, "ctr": 0, "position": 0}
    return {"url": url, "debut": debut, "fin": fin_txt,
            "clics": round(r["clicks"]), "impressions": round(r["impressions"]),
            "ctr": round(r["ctr"] * 100, 2), "position": round(r["position"], 1) if r["position"] else None}


def variation_temoin(avant_fin: dt.date, apres_fin: dt.date, exclure: set[str],
                     jours: int = 28, site: str | None = None) -> dict:
    """Variation des clics des pages NON modifiées entre deux fenêtres.

    C'est la référence qui neutralise la saisonnalité et les mises à jour
    Google : si tout le site a pris +12 %, une page modifiée à +17 % n'a
    gagné que 5 points grâce à la modification.
    """
    site = site or site_par_defaut()

    def total(fin: dt.date) -> tuple[int, int]:
        debut, fin_txt = fenetre(jours, fin)
        lignes = requete(site, ["page"], debut, fin_txt, 100000)
        gardees = [r for r in lignes if r["keys"][0] not in exclure]
        return round(sum(r["clicks"] for r in gardees)), len(gardees)

    clics_avant, pages = total(avant_fin)
    clics_apres, _ = total(apres_fin)
    variation = (clics_apres - clics_avant) / clics_avant * 100 if clics_avant else 0.0
    return {"clics_avant": clics_avant, "clics_apres": clics_apres, "pages": pages,
            "variation_pct": round(variation, 1)}


# ─── Commandes ────────────────────────────────────────────────────

def cmd_sites(a) -> None:
    d = appel(f"{API}/sites")
    lignes = sorted((s["siteUrl"], s.get("permissionLevel", "")) for s in d.get("siteEntry", []))
    print(f"{len(lignes)} propriété(s) :\n")
    for u, p in lignes:
        print(f"  {u:<48} {p}")


def cmd_perf(a) -> None:
    site = a.site or site_par_defaut()
    debut, fin = fenetre(a.jours)
    dims = [] if a.par == "total" else [a.par]
    lignes = requete(site, dims, debut, fin, a.lignes)
    if a.json:
        print(json.dumps({"site": site, "debut": debut, "fin": fin, "rows": lignes}, ensure_ascii=False))
        return
    print(f"\n{site} · {debut} → {fin} ({a.jours} jours)")
    avant = {}
    if a.compare:
        precedente = dt.date.fromisoformat(debut) - dt.timedelta(days=1)
        d2, f2 = fenetre(a.jours, precedente)
        avant = {tuple(r.get("keys", [])): r for r in requete(site, dims, d2, f2, a.lignes)}
        print(f"comparé à {d2} → {f2}")
    print()
    if not lignes:
        print("  aucune donnée sur la période")
        return
    if a.par == "total":
        r = lignes[0]
        print(f"  clics        {r['clicks']:>10,.0f}\n  impressions  {r['impressions']:>10,.0f}")
        print(f"  CTR          {r['ctr']*100:>9.2f} %\n  position     {r['position']:>10.1f}")
        if avant:
            b = list(avant.values())[0]
            print(f"\n  évolution    clics {r['clicks']-b['clicks']:+,.0f} · "
                  f"impressions {r['impressions']-b['impressions']:+,.0f} · "
                  f"position {b['position']-r['position']:+.1f}")
        return
    lg = min(max((len(r["keys"][0]) for r in lignes), default=10), 62)
    print(f"  {'':<{lg}} {'clics':>7} {'impr.':>9} {'CTR':>7} {'pos.':>6}" + ("  évol. clics" if avant else ""))
    for r in lignes:
        k = r["keys"][0]
        k = k[:lg - 1] + "…" if len(k) > lg else k
        ligne = f"  {k:<{lg}} {r['clicks']:>7,.0f} {r['impressions']:>9,.0f} {r['ctr']*100:>6.1f}% {r['position']:>6.1f}"
        if avant:
            b = avant.get(tuple(r["keys"]))
            ligne += f"  {r['clicks']-b['clicks']:+8,.0f}" if b else "      nouveau"
        print(ligne)


def cmd_page(a) -> None:
    fin = dt.date.fromisoformat(a.fin) if a.fin else None
    print(json.dumps(mesures_page(a.url, fin, a.jours, a.site), ensure_ascii=False, indent=1))


def cmd_instantane(a) -> None:
    """Instantané page × requête des 28 derniers jours, pour décider sur des chiffres."""
    site = a.site or site_par_defaut()
    debut, fin = fenetre(a.jours)
    lignes = requete(site, ["page", "query"], debut, fin, a.lignes)
    annee, semaine, _ = dt.date.fromisoformat(fin).isocalendar()
    sortie = Path(a.sortie) if a.sortie else racine_projet() / "donnees" / f"{annee}-S{semaine:02d}.json"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(json.dumps({
        "site": site, "debut": debut, "fin": fin, "genere_le": dt.datetime.now().isoformat(timespec="seconds"),
        "lignes": [{"page": r["keys"][0], "requete": r["keys"][1], "clics": r["clicks"],
                    "impressions": r["impressions"], "ctr": round(r["ctr"] * 100, 2),
                    "position": round(r["position"], 1)} for r in lignes],
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  ✓ {len(lignes)} lignes page × requête ({debut} → {fin}) → {sortie}")


def cmd_temoin(a) -> None:
    exclure = set()
    if a.exclure:
        exclure = {u.strip() for u in Path(a.exclure).read_text(encoding="utf-8").splitlines() if u.strip()}
    r = variation_temoin(dt.date.fromisoformat(a.avant_fin), dt.date.fromisoformat(a.apres_fin),
                         exclure, a.jours, a.site)
    print(json.dumps(r, ensure_ascii=False, indent=1))


def cmd_sitemap(a) -> None:
    """Resoumettre ne force pas l'indexation : ça redit à Google « regarde ici ».
    L'Indexing API ne couvre que JobPosting et BroadcastEvent ; l'utiliser pour
    autre chose est hors des règles."""
    site = a.site or site_par_defaut()
    base = f"{API}/sites/{urllib.parse.quote(site, safe='')}/sitemaps"
    smaps = appel(base).get("sitemap", [])
    print(f"\n{len(smaps)} sitemap(s) déclaré(s) :\n")
    for sm in smaps:
        # L'API renvoie des nombres en chaînes : « "0" » est vrai en Python.
        err, avert = int(sm.get("errors", 0)), int(sm.get("warnings", 0))
        detail = " · ".join(f"{int(c.get('submitted', 0))} {c['type']}" for c in sm.get("contents", []))
        etat = "✓ sain" if not err and not avert else f"✗ {err} erreur(s), {avert} avertissement(s)"
        print(f"  {sm['path']}\n      {detail} · téléchargé le {sm.get('lastDownloaded', 'jamais')[:10]} · {etat}")
    if a.resoumettre:
        print()
        for sm in smaps:
            try:
                appel(f"{base}/{urllib.parse.quote(sm['path'], safe='')}", methode="PUT", ecriture=True)
                print(f"  ✓ resoumis : {sm['path']}")
            except ErreurGSC as exc:
                print(f"  ✗ {sm['path']} : {exc}")


def cmd_inspect(a) -> None:
    site = a.site or site_par_defaut()
    urls = a.url or [u.strip() for u in open(a.fichier, encoding="utf-8") if u.strip()]
    prefixe = site.rstrip("/") if site.startswith("http") else ""
    print(f"\n{len(urls)} URL à inspecter · quota 2 000/jour\n")
    compte: dict[str, int] = {}
    for u in urls:
        r = appel(INSPECT, {"inspectionUrl": u, "siteUrl": site, "languageCode": "fr"}) \
            .get("inspectionResult", {}).get("indexStatusResult", {})
        verdict, couverture = r.get("verdict", "?"), r.get("coverageState", "")
        compte[couverture or verdict] = compte.get(couverture or verdict, 0) + 1
        court = u.replace(prefixe, "") if prefixe else u
        print(f"  {({'PASS': '✓', 'NEUTRAL': '•', 'FAIL': '✗'}).get(verdict, '?')} {court:<48} {couverture}")
        if r.get("lastCrawlTime"):
            canon = (r.get("googleCanonical") or "—").replace(prefixe, "") if prefixe else r.get("googleCanonical")
            print(f"      dernier passage : {r['lastCrawlTime'][:10]} · robots : {r.get('robotsTxtState', '')}"
                  f" · canonique Google : {canon}")
    print("\n  Récapitulatif :")
    for k, v in sorted(compte.items(), key=lambda x: -x[1]):
        print(f"    {v:>3} · {k}")


def main() -> int:
    charger_env()
    ap = argparse.ArgumentParser(description="Search Console en direct")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("sites", help="propriétés accessibles").set_defaults(f=cmd_sites)

    p = sub.add_parser("perf", help="clics, impressions, CTR, position")
    p.add_argument("--site"); p.add_argument("--jours", type=int, default=28)
    p.add_argument("--par", default="total", choices=["total", "page", "query", "date", "country", "device"])
    p.add_argument("--lignes", type=int, default=25)
    p.add_argument("--compare", action="store_true", help="comparer à la période précédente")
    p.add_argument("--json", action="store_true")
    p.set_defaults(f=cmd_perf)

    p = sub.add_parser("page", help="mesures d'une URL, en JSON (utilisé par journal.py)")
    p.add_argument("--url", required=True); p.add_argument("--site")
    p.add_argument("--jours", type=int, default=28); p.add_argument("--fin", help="AAAA-MM-JJ")
    p.set_defaults(f=cmd_page)

    p = sub.add_parser("instantane", help="instantané page × requête → donnees/")
    p.add_argument("--site"); p.add_argument("--jours", type=int, default=28)
    p.add_argument("--lignes", type=int, default=25000); p.add_argument("--sortie")
    p.set_defaults(f=cmd_instantane)

    p = sub.add_parser("temoin", help="variation des clics des pages non modifiées")
    p.add_argument("--avant-fin", required=True); p.add_argument("--apres-fin", required=True)
    p.add_argument("--exclure", help="fichier : une URL modifiée par ligne")
    p.add_argument("--site"); p.add_argument("--jours", type=int, default=28)
    p.set_defaults(f=cmd_temoin)

    p = sub.add_parser("sitemap", help="état des sitemaps, et resoumission")
    p.add_argument("--site"); p.add_argument("--resoumettre", action="store_true")
    p.set_defaults(f=cmd_sitemap)

    p = sub.add_parser("inspect", help="état d'indexation (API URL Inspection)")
    p.add_argument("--site"); p.add_argument("--url", nargs="*"); p.add_argument("--fichier")
    p.set_defaults(f=cmd_inspect)

    a = ap.parse_args()
    try:
        a.f(a)
    except ErreurGSC as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
