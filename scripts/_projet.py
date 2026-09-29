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


def _lignes_config() -> list[str]:
    config = fichier_config()
    return config.read_text(encoding="utf-8").splitlines() if config else []


def _trouver(chemin: str) -> tuple[int, str, list[str]] | None:
    """Localise `a.b.c` dans la config en respectant l'imbrication.

    Renvoie (index de ligne, valeur brute, lignes), ou None. Lecture
    volontairement minimale, sans PyYAML : les garde-fous doivent tourner
    partout. Mais elle respecte l'imbrication — `publication.mode` et `mode`
    sont deux clés différentes ; les confondre plaçait tout projet en code en
    mode safe.
    """
    lignes = _lignes_config()
    parties = chemin.split(".")
    debut, retrait_parent = 0, -1
    for profondeur, cle in enumerate(parties):
        trouve, retrait_niveau = None, None
        for i in range(debut, len(lignes)):
            texte = lignes[i].split(" #", 1)[0].rstrip()
            if not texte.strip() or texte.lstrip().startswith("#"):
                continue
            retrait = len(texte) - len(texte.lstrip())
            if retrait <= retrait_parent:
                break                                   # fin du bloc parent
            if retrait_niveau is None:
                retrait_niveau = retrait                # le niveau de ce bloc
            if retrait == retrait_niveau and texte.strip().startswith(f"{cle}:"):
                trouve = (i, retrait, texte.split(":", 1)[1].strip())
                break
        if trouve is None:
            return None
        i, retrait, valeur = trouve
        if profondeur == len(parties) - 1:
            return i, valeur, lignes
        debut, retrait_parent = i + 1, retrait
    return None


def lire_valeur(chemin: str, defaut: str = "") -> str:
    """Valeur scalaire au chemin `a.b` (ex. `mode`, `publication.mode`)."""
    trouve = _trouver(chemin)
    if not trouve:
        return defaut
    valeur = trouve[1].strip().strip("\"'")
    return valeur if valeur else defaut


def lire_liste(chemin: str) -> list[str]:
    """Liste au chemin `a.b`, en blocs (« - valeur ») ou en ligne (« [a, b] »)."""
    trouve = _trouver(chemin)
    if not trouve:
        return []
    i, en_ligne, lignes = trouve
    if en_ligne.startswith("["):
        return [v.strip().strip("\"'") for v in en_ligne.strip("[]").split(",") if v.strip()]
    retrait = len(lignes[i]) - len(lignes[i].lstrip())
    valeurs = []
    for suite in lignes[i + 1:]:
        if not suite.strip() or suite.strip().startswith("#"):
            continue
        if len(suite) - len(suite.lstrip()) <= retrait:
            break
        item = suite.strip()
        if item.startswith("- "):
            valeurs.append(item[2:].split(" #", 1)[0].strip().strip("\"'"))
    return valeurs
