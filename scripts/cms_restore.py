#!/usr/bin/env python3
"""Restaure un contenu CMS depuis une sauvegarde produite avant écriture.

    python3 scripts/cms_restore.py .seo-decupler/backups/2026-03-14-1032-page.json
    python3 scripts/cms_restore.py --lister

Les sauvegardes sont créées automatiquement par seo-publication-cms avant
toute modification. C'est le filet de sécurité du mode autonomous.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import charger_env, dossier_etat  # noqa: E402

# Les sauvegardes vivent dans le projet : dans le dossier du plugin, elles
# disparaîtraient à la première mise à jour — avec le filet de sécurité.
DOSSIER = dossier_etat("backups")



def lister() -> int:
    if not DOSSIER.exists():
        print("\n  Aucune sauvegarde. Elles sont créées automatiquement avant")
        print("  chaque écriture sur un CMS.\n")
        return 0
    fichiers = sorted(DOSSIER.glob("*.json"), reverse=True)
    print(f"\n  {len(fichiers)} sauvegarde(s) :\n")
    for f in fichiers[:30]:
        try:
            donnees = json.loads(f.read_text(encoding="utf-8"))
            print(f"    {f.name}")
            print(f"      {donnees.get('cms', '?')} · {donnees.get('titre', 'sans titre')[:50]}")
            print(f"      {donnees.get('url', '')}\n")
        except (json.JSONDecodeError, OSError):
            print(f"    {f.name}  (illisible)\n")
    return 0


def restaurer(chemin: Path) -> int:
    try:
        import requests
    except ImportError:
        print("Dépendance manquante : pip install -r requirements.txt", file=sys.stderr)
        return 1

    donnees = json.loads(chemin.read_text(encoding="utf-8"))
    cms = donnees.get("cms", "").lower()
    charger_env()

    print(f"\n  Restauration depuis {chemin.name}")
    print(f"  CMS       : {cms}")
    print(f"  Contenu   : {donnees.get('titre', 'sans titre')}")
    print(f"  URL       : {donnees.get('url', '—')}")
    print(f"  Sauvegardé: {donnees.get('date', '—')}\n")

    reponse = input("  Confirmer la restauration ? [oui/non] ").strip().lower()
    if reponse not in ("oui", "o", "yes", "y"):
        print("  Annulé.\n")
        return 0

    if cms == "wordpress":
        site = os.environ.get("WP_SITE_URL", "").rstrip("/")
        utilisateur = os.environ.get("WP_USERNAME", "")
        motdepasse = os.environ.get("WP_APP_PASSWORD", "")
        if not all([site, utilisateur, motdepasse]):
            print("  ✗ Identifiants WordPress absents dans .env\n")
            return 1

        type_contenu = donnees.get("type", "posts")
        identifiant = donnees.get("id")
        charge = {c: donnees[c] for c in
                  ("title", "content", "excerpt", "status", "slug", "categories", "tags")
                  if c in donnees}

        rep = requests.post(f"{site}/wp-json/wp/v2/{type_contenu}/{identifiant}",
                            auth=(utilisateur, motdepasse), json=charge, timeout=30)
        if rep.status_code < 300:
            print(f"  ✓ Restauré. Vérifiez : {donnees.get('url')}\n")
            return 0
        print(f"  ✗ Échec ({rep.status_code}) : {rep.text[:200]}\n")
        return 1

    if cms == "webflow":
        jeton = os.environ.get("WEBFLOW_TOKEN", "")
        if not jeton:
            print("  ✗ WEBFLOW_TOKEN absent dans .env\n")
            return 1
        rep = requests.patch(
            f"https://api.webflow.com/v2/collections/{donnees['collection_id']}"
            f"/items/{donnees['id']}",
            headers={"Authorization": f"Bearer {jeton}", "Content-Type": "application/json"},
            json={"fieldData": donnees.get("fieldData", {})}, timeout=30)
        if rep.status_code < 300:
            print("  ✓ Restauré. Pensez à republier le site dans Webflow.\n")
            return 0
        print(f"  ✗ Échec ({rep.status_code}) : {rep.text[:200]}\n")
        return 1

    print(f"  CMS « {cms} » non géré automatiquement.")
    print(f"  Le contenu d'origine est dans {chemin} — restaurez-le à la main.\n")
    return 1


def main() -> int:
    p = argparse.ArgumentParser(description="Restauration CMS")
    p.add_argument("sauvegarde", nargs="?", help="chemin du fichier de sauvegarde")
    p.add_argument("--lister", action="store_true")
    args = p.parse_args()

    if args.lister or not args.sauvegarde:
        return lister()

    chemin = Path(args.sauvegarde)
    if not chemin.exists():
        chemin = DOSSIER / args.sauvegarde
    if not chemin.exists():
        print(f"Sauvegarde introuvable : {args.sauvegarde}", file=sys.stderr)
        return 1
    return restaurer(chemin)


if __name__ == "__main__":
    sys.exit(main())
