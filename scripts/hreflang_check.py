#!/usr/bin/env python3
"""Validation hreflang — auto-référence, réciprocité, codes, canonicals.

    python3 scripts/hreflang_check.py https://exemple.com/fr/page
"""

from __future__ import annotations

import argparse
import re
import sys

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Dépendances manquantes : pip install -r requirements.txt", file=sys.stderr)
    raise SystemExit(1)

AGENT = "ClaudeCodeSEODecupler/2.0 (+https://decupler.com)"

# ISO 639-1 : les codes langue les plus courants. La liste complète est longue ;
# ceux-ci couvrent l'immense majorité des cas réels.
LANGUES = {
    "fr", "en", "de", "es", "it", "pt", "nl", "pl", "ru", "ja", "zh", "ar", "ko",
    "sv", "da", "no", "fi", "cs", "el", "tr", "he", "hi", "th", "vi", "id", "uk",
    "ro", "hu", "bg", "hr", "sk", "sl", "lt", "lv", "et", "ca", "eu", "gl",
}

# Confusions fréquentes, avec le code correct.
CORRECTIONS = {
    "uk": ("en-GB", "le code du Royaume-Uni est GB, pas UK (UK n'existe pas en ISO 3166-1)"),
    "eu": ("un code pays réel", "EU n'est pas un pays"),
    "gb": ("GB", None),
}


def recuperer(url: str) -> tuple[list[dict], str]:
    rep = requests.get(url, headers={"User-Agent": AGENT}, timeout=30)
    rep.raise_for_status()
    soup = BeautifulSoup(rep.text, "html.parser")

    alternatives = []
    for lien in soup.find_all("link", attrs={"rel": re.compile("^alternate$", re.I)}):
        code = lien.get("hreflang")
        if code:
            alternatives.append({"hreflang": code.strip(), "href": (lien.get("href") or "").strip()})

    canon = soup.find("link", attrs={"rel": re.compile("^canonical$", re.I)})
    return alternatives, (canon.get("href", "").strip() if canon else "")


def valider_code(code: str) -> str | None:
    if code.lower() == "x-default":
        return None
    if "_" in code:
        return f"« {code} » utilise un underscore. Le séparateur est un tiret : {code.replace('_', '-')}"

    parties = code.split("-")
    langue = parties[0].lower()

    if len(langue) == 3:
        return f"« {langue} » semble être un code ISO 639-2 (3 lettres). Utilisez le code à 2 lettres."
    if langue not in LANGUES:
        if langue in CORRECTIONS:
            correct, raison = CORRECTIONS[langue]
            return f"« {code} » : {raison or 'code langue invalide'}. Attendu : {correct}"
        return f"« {langue} » n'est pas un code langue ISO 639-1 reconnu"

    if len(parties) == 1:
        return None
    region = parties[1]
    if region.lower() == "uk":
        return f"« {code} » : le code du Royaume-Uni est GB. Écrivez {langue}-GB"
    if len(region) == 3:
        return f"« {code} » : code pays à 3 lettres. ISO 3166-1 alpha-2 attendu (2 lettres)"
    if len(region) == 2 and not region.isupper():
        return f"« {code} » : la région s'écrit en majuscules — {langue}-{region.upper()}"
    if len(parties) > 2:
        return f"« {code} » : format inattendu. Utilisez langue ou langue-RÉGION"
    return None


def main() -> int:
    p = argparse.ArgumentParser(description="Validation hreflang")
    p.add_argument("url")
    p.add_argument("--verifier-retours", action="store_true",
                   help="vérifie que chaque page alternative déclare bien celle-ci en retour")
    args = p.parse_args()

    alternatives, canonical = recuperer(args.url)

    print(f"\n{'═' * 60}")
    print(f"  Hreflang — {args.url}")
    print(f"{'═' * 60}\n")

    if not alternatives:
        print("  ℹ️  Aucune balise hreflang. Normal sur un site monolingue.\n")
        return 0

    print(f"  {len(alternatives)} alternative(s) déclarée(s) :\n")
    for a in alternatives:
        print(f"    {a['hreflang']:<12} {a['href']}")
    print()

    erreurs = []

    for a in alternatives:
        souci = valider_code(a["hreflang"])
        if souci:
            erreurs.append(("🔴", souci))
        if a["href"] and not a["href"].startswith("http"):
            erreurs.append(("🔴", f"« {a['hreflang'] } » utilise une URL relative. "
                                  "Les hreflang exigent des URL absolues."))

    # Auto-référence : la page doit figurer dans sa propre liste.
    url_nue = args.url.rstrip("/")
    auto = any(a["href"].rstrip("/") == url_nue for a in alternatives)
    if not auto:
        erreurs.append(("🔴", "Auto-référence absente. Chaque page doit se déclarer "
                              "elle-même dans sa liste, sinon le groupe entier est ignoré."))

    if not any(a["hreflang"].lower() == "x-default" for a in alternatives):
        erreurs.append(("🟠", "x-default absent. Recommandé pour les visiteurs dont la "
                              "langue n'est pas couverte."))

    # Canonical cross-langue : l'erreur la plus coûteuse.
    if canonical and canonical.rstrip("/") != url_nue:
        cible = next((a for a in alternatives if a["href"].rstrip("/") == canonical.rstrip("/")), None)
        if cible:
            erreurs.append(("🔴", f"La canonical pointe vers la version « {cible['hreflang']} » "
                                  "au lieu de la page elle-même. Cela annule tout le hreflang : "
                                  "Google ne gardera qu'une seule version."))

    codes = [a["hreflang"].lower() for a in alternatives]
    for code in set(codes):
        if codes.count(code) > 1:
            erreurs.append(("🔴", f"« {code} » déclaré {codes.count(code)} fois."))

    if args.verifier_retours:
        print("  Vérification des liens retour…\n")
        for a in alternatives:
            if a["href"].rstrip("/") == url_nue:
                continue
            try:
                autres, _ = recuperer(a["href"])
                if not any(x["href"].rstrip("/") == url_nue for x in autres):
                    erreurs.append(("🔴", f"« {a['hreflang']} » ne déclare pas de lien retour "
                                          "vers cette page. La paire entière est invalidée."))
            except Exception as exc:
                erreurs.append(("🟠", f"« {a['hreflang']} » inaccessible : {str(exc)[:80]}"))

    if erreurs:
        print("─── Problèmes ───\n")
        for icone, message in erreurs:
            print(f"  {icone} {message}\n")
    else:
        print("  🟢 Aucun problème détecté.\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
