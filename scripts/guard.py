#!/usr/bin/env python3
"""Garde-fou central de Claude Code SEO Décupler.

Tout skill qui s'apprête à écrire quelque part (CMS, fichier de prod,
plateforme externe) appelle ce script d'abord. Il répond AUTORISE,
DEMANDE_VALIDATION ou BLOQUE, et dit pourquoi.

    python3 scripts/guard.py --action publier --cible https://exemple.com/page
    python3 scripts/guard.py --action generer-pages --volume 240
    python3 scripts/guard.py --statut

Codes de sortie : 0 = autorisé, 1 = validation requise, 2 = bloqué.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import charger_env, config_est_le_modele, fichier_config, racine_projet  # noqa: E402

# Le kill-switch doit voir SEO_SAFE_MODE même quand il n'est écrit que dans
# le .env du projet — c'est là que la documentation dit de le mettre.
charger_env()
CONFIG = fichier_config()

# Un kill-switch doit se déclencher sur toutes les façons raisonnables
# d'écrire « oui » : quelqu'un qui tape SEO_SAFE_MODE=true s'attend à être
# protégé.
VALEURS_VRAIES = {"1", "true", "yes", "oui", "on"}

# Actions qui écrivent quelque part hors de la machine locale.
ACTIONS_ECRITURE = {
    "publier",
    "mettre-a-jour-page",
    "modifier-robots",
    "modifier-redirections",
    "modifier-canonical",
    "poster-communaute",
    "envoyer-email",
    "supprimer-contenu",
    "generer-pages",
}

# Actions qui exigent toujours un humain, quel que soit le mode.
ACTIONS_VALIDATION_OBLIGATOIRE = {
    "poster-communaute",
    "envoyer-email",
}

# Actions interdites en toutes circonstances.
ACTIONS_INTERDITES = {
    "supprimer-contenu",
}


def _lire_config() -> dict:
    """Lecture minimaliste du YAML — volontairement sans dépendance.

    On ne lit que les clés scalaires dont le garde-fou a besoin, ce qui
    évite d'imposer PyYAML pour faire tourner le kill-switch.
    """
    valeurs: dict[str, str] = {}
    if CONFIG is None:
        return valeurs
    for ligne in CONFIG.read_text(encoding="utf-8").splitlines():
        nue = ligne.split("#", 1)[0].strip()
        if not nue or ":" not in nue:
            continue
        cle, _, valeur = nue.partition(":")
        valeur = valeur.strip().strip("\"'")
        if valeur:
            valeurs[cle.strip()] = valeur
    return valeurs


def mode_effectif() -> tuple[str, str]:
    """Renvoie (mode, raison). SEO_SAFE_MODE prend le pas sur tout."""
    if os.environ.get("SEO_SAFE_MODE", "0").strip().lower() in VALEURS_VRAIES:
        return "safe", "SEO_SAFE_MODE activé (environnement ou .env du projet)"
    if "--safe" in sys.argv:
        return "safe", "flag --safe passé à la commande"
    if CONFIG is None:
        return "safe", "aucune configuration trouvée — repli sur safe"
    config = _lire_config()
    mode = config.get("mode", "safe")
    if mode not in {"safe", "assisted", "autonomous"}:
        return "safe", f"mode '{mode}' inconnu dans {CONFIG.name} — repli sur safe"
    if config_est_le_modele():
        return mode, "modèle par défaut du plugin — aucune config propre à ce projet"
    try:
        source = str(CONFIG.relative_to(racine_projet()))
    except ValueError:
        source = str(CONFIG)
    return mode, source


def domaines_autorises() -> list[str]:
    bruts = os.environ.get("SEO_ALLOWED_DOMAINS", "").strip()
    if bruts:
        return [d.strip().lower().removeprefix("www.") for d in bruts.split(",") if d.strip()]
    site = os.environ.get("GSC_SITE_URL", "").strip()
    if site:
        hote = urlparse(site).netloc.lower().removeprefix("www.")
        if hote:
            return [hote]
    config = _lire_config()
    domaine = config.get("domaine", "").strip().lower()
    if domaine:
        hote = urlparse(domaine if "//" in domaine else f"https://{domaine}").netloc
        return [hote.removeprefix("www.")] if hote else []
    return []


def _seuil(config: dict, cle: str, defaut: int) -> int:
    try:
        return int(config.get(cle, defaut))
    except (TypeError, ValueError):
        return defaut


def evaluer(action: str, cible: str | None, volume: int | None) -> tuple[str, str]:
    """Renvoie (verdict, explication)."""
    mode, source_mode = mode_effectif()
    config = _lire_config()

    if action in ACTIONS_INTERDITES:
        return "BLOQUE", (
            f"L'action « {action} » est interdite par un garde-fou dur. "
            "Dépubliez ou repassez en brouillon plutôt que de supprimer — "
            "une suppression est irréversible et casse les liens entrants."
        )

    if action not in ACTIONS_ECRITURE:
        return "AUTORISE", f"« {action} » est une action de lecture, sans effet de bord."

    if mode == "safe":
        return "BLOQUE", (
            f"Mode safe actif ({source_mode}). Aucune écriture externe. "
            "Le livrable sera produit en local, à vous de le poser où vous voulez."
        )

    if action in ACTIONS_VALIDATION_OBLIGATOIRE:
        return "DEMANDE_VALIDATION", (
            f"« {action} » engage votre identité publique ou votre compte. "
            "Validation humaine obligatoire, y compris en mode autonomous."
        )

    if action == "generer-pages" and volume is not None:
        blocage = _seuil(config, "pages_programmatiques_blocage", 500)
        alerte = _seuil(config, "pages_programmatiques_alerte", 100)
        if volume >= blocage:
            return "BLOQUE", (
                f"{volume} pages demandées, seuil de blocage à {blocage}. "
                "À ce volume, Google évalue le lot entier, pas page par page : "
                "un échantillon de 20 pages doit passer un audit qualité avant "
                "de lancer le reste. Lancez `/seo programmatique audit` d'abord."
            )
        if volume >= alerte:
            return "DEMANDE_VALIDATION", (
                f"{volume} pages demandées, seuil d'alerte à {alerte}. "
                "Vérifiez que chaque page apporte une valeur propre et non une "
                "simple permutation de variables, sinon c'est du contenu mince à l'échelle."
            )

    if config.get("domaines_autorises_uniquement", "true") == "true":
        autorises = domaines_autorises()
        if not autorises:
            return "BLOQUE", (
                "Aucun domaine d'écriture autorisé n'est configuré, donc toute "
                "écriture externe est refusée — c'est le comportement voulu tant "
                "que la cible n'est pas déclarée. Renseignez GSC_SITE_URL ou "
                "SEO_ALLOWED_DOMAINS dans .env, ou projet.domaine dans "
                "config/decupler-seo.config.yml."
            )
        hote = urlparse(cible or "").netloc.lower().removeprefix("www.")
        if not hote:
            return "DEMANDE_VALIDATION", (
                f"« {action} » sans cible identifiable. Précisez l'URL visée "
                f"pour que le domaine puisse être vérifié contre la liste "
                f"autorisée ({', '.join(autorises)})."
            )
        if hote not in autorises:
            return "BLOQUE", (
                f"Le domaine « {hote} » n'est pas dans la liste autorisée "
                f"({', '.join(autorises)}). Ajoutez-le à SEO_ALLOWED_DOMAINS "
                "si l'écriture est bien intentionnelle."
            )

    if mode == "assisted":
        return "DEMANDE_VALIDATION", (
            f"Mode assisted ({source_mode}) : « {action} » est autorisée "
            "mais attend votre feu vert."
        )

    return "AUTORISE", f"Mode autonomous ({source_mode}). Garde-fous vérifiés, action permise."


def statut() -> dict:
    mode, source = mode_effectif()
    config = _lire_config()
    return {
        "mode": mode,
        "source": source,
        "domaines_autorises": domaines_autorises() or ["(aucun — écriture externe bloquée)"],
        "statut_publication_par_defaut": config.get("statut_par_defaut", "draft"),
        "cms": config.get("cms", "aucun"),
        "seuils": {
            "pages_programmatiques_alerte": _seuil(config, "pages_programmatiques_alerte", 100),
            "pages_programmatiques_blocage": _seuil(config, "pages_programmatiques_blocage", 500),
            "pages_locales_alerte": _seuil(config, "pages_locales_alerte", 30),
            "pages_locales_blocage": _seuil(config, "pages_locales_blocage", 50),
        },
        "garde_fous_durs": sorted(ACTIONS_INTERDITES | ACTIONS_VALIDATION_OBLIGATOIRE),
    }


def main() -> int:
    parseur = argparse.ArgumentParser(description="Garde-fou Claude Code SEO Décupler")
    parseur.add_argument("--action", help=f"une de : {', '.join(sorted(ACTIONS_ECRITURE))}")
    parseur.add_argument("--cible", help="URL visée par l'action")
    parseur.add_argument("--volume", type=int, help="nombre de pages, pour generer-pages")
    parseur.add_argument("--statut", action="store_true", help="affiche l'état du garde-fou")
    parseur.add_argument("--safe", action="store_true", help="force le mode safe pour cet appel")
    args = parseur.parse_args()

    if args.statut or not args.action:
        print(json.dumps(statut(), ensure_ascii=False, indent=2))
        return 0

    verdict, explication = evaluer(args.action, args.cible, args.volume)
    print(json.dumps(
        {"verdict": verdict, "action": args.action, "cible": args.cible, "explication": explication},
        ensure_ascii=False, indent=2,
    ))
    return {"AUTORISE": 0, "DEMANDE_VALIDATION": 1, "BLOQUE": 2}[verdict]


if __name__ == "__main__":
    sys.exit(main())
