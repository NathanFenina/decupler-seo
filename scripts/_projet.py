"""Où trouver la configuration, les clés et l'état — pour tous les scripts.

Le plugin est installé une fois et sert à plusieurs projets (vos sites, vos
clients). La configuration et l'état appartiennent donc au PROJET, pas au
plugin : le dossier du plugin change à chaque mise à jour, et tout ce qui y
serait écrit disparaîtrait avec l'ancienne version.

Ordre de recherche de la configuration :
    1. $SEO_DECUPLER_CONFIG                       — chemin explicite
    2. ./decupler-seo.config.yml                  — à la racine du projet
    3. ./config/decupler-seo.config.yml           — dans un clone du dépôt
    4. <plugin>/config/decupler-seo.config.yml    — modèle par défaut, lecture seule

Le « projet », c'est le dossier depuis lequel Claude est lancé, ou
$SEO_DECUPLER_PROJET s'il est défini.
"""

from __future__ import annotations

import os
from pathlib import Path

RACINE_PLUGIN = Path(__file__).resolve().parent.parent
NOM_CONFIG = "decupler-seo.config.yml"


def racine_projet() -> Path:
    explicite = os.environ.get("SEO_DECUPLER_PROJET", "").strip()
    return Path(explicite).expanduser().resolve() if explicite else Path.cwd()


def fichier_config() -> Path | None:
    explicite = os.environ.get("SEO_DECUPLER_CONFIG", "").strip()
    projet = racine_projet()
    candidats = [Path(explicite).expanduser()] if explicite else []
    candidats += [
        projet / NOM_CONFIG,
        projet / "config" / NOM_CONFIG,
        RACINE_PLUGIN / "config" / NOM_CONFIG,
    ]
    return next((c for c in candidats if c.is_file()), None)


def config_est_le_modele() -> bool:
    """Vrai si aucune config projet n'existe et qu'on lit le modèle du plugin."""
    trouve = fichier_config()
    return trouve is not None and trouve.resolve() == (RACINE_PLUGIN / "config" / NOM_CONFIG).resolve()


def charger_env() -> list[Path]:
    """Charge les .env sans écraser l'environnement réel.

    Le .env du projet est lu en premier, donc il l'emporte sur celui du
    plugin. Renvoie les fichiers effectivement lus.
    """
    lus = []
    for fichier in (racine_projet() / ".env", RACINE_PLUGIN / ".env"):
        if not fichier.is_file():
            continue
        for ligne in fichier.read_text(encoding="utf-8").splitlines():
            nue = ligne.strip()
            if nue and not nue.startswith("#") and "=" in nue:
                cle, _, valeur = nue.partition("=")
                os.environ.setdefault(cle.strip(), valeur.strip().strip("\"'"))
        lus.append(fichier)
    return lus


def dossier_etat(*sous_dossiers: str) -> Path:
    """Dossier d'état du projet (sauvegardes, historique). Jamais dans le plugin."""
    return racine_projet().joinpath(".seo-decupler", *sous_dossiers)


def resoudre(chemin: str) -> Path:
    """Résout un chemin de la config (ex. un fichier de clé) depuis le projet."""
    p = Path(chemin).expanduser()
    return p if p.is_absolute() else racine_projet() / p
