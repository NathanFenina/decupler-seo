#!/usr/bin/env python3
"""Crée un projet SEO et y synchronise la méthode decupler-seo.

    python3 scripts/projet.py init ../mon-projet --nom "Mon Projet" --domaine https://exemple.com
    python3 scripts/projet.py sync ../mon-projet
    python3 scripts/projet.py sync . --depuis https://github.com/NathanFenina/decupler-seo
    python3 scripts/projet.py statut ../mon-projet

Pourquoi embarquer la méthode dans chaque projet : une routine Claude Code
tourne dans une session cloud qui ne charge pas les plugins installés via
marketplace. Elle ne voit que ce qui est commité dans le dépôt cloné :
CLAUDE.md, .claude/skills, .claude/agents, .claude/commands et .mcp.json.

Ce qui appartient au projet n'est jamais touché par la synchronisation :
la mémoire, la config, le journal, les données, et les skills préfixés
`projet-`. Ce qui appartient à la méthode est remplacé à chaque synchro,
après vérification qu'aucun fichier n'a été modifié localement — sinon la
modification serait perdue sans que personne ne le sache.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

RACINE_METHODE = Path(__file__).resolve().parent.parent
DEPOT_DEFAUT = "https://github.com/NathanFenina/decupler-seo"
MODELE = "modele-projet"
DOSSIER_EMBARQUE = Path(".claude") / "decupler-seo"
MANIFESTE = DOSSIER_EMBARQUE / "FICHIERS.json"
PREFIXE_PROJET = "projet-"
JETON = "${CLAUDE_PLUGIN_ROOT}"

# Ressources de la méthode copiées sous .claude/decupler-seo/.
RESSOURCES = ("scripts", "schema", "templates", "config", "hooks")


# ─── Utilitaires ──────────────────────────────────────────────────

def empreinte(fichier: Path) -> str:
    return hashlib.sha256(fichier.read_bytes()).hexdigest()[:16]


def version_de(source: Path) -> str:
    try:
        v = json.loads((source / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
    except (OSError, KeyError, json.JSONDecodeError):
        v = "inconnue"
    try:
        sha = subprocess.run(["git", "-C", str(source), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        sha = ""
    return f"{v}+{sha}" if sha else v


def obtenir_source(depuis: str | None) -> tuple[Path, tempfile.TemporaryDirectory | None]:
    """Renvoie le dossier de la méthode à copier : local, ou cloné depuis une URL."""
    if not depuis:
        if (RACINE_METHODE / "skills").is_dir():
            return RACINE_METHODE, None
        # Lancé depuis la copie embarquée d'un projet : elle ne contient pas
        # les skills sources, on récupère donc la dernière version publiée.
        depuis = DEPOT_DEFAUT
        print(f"  Source : {DEPOT_DEFAUT}")
    if Path(depuis).expanduser().is_dir():
        return Path(depuis).expanduser().resolve(), None
    tempo = tempfile.TemporaryDirectory(prefix="decupler-seo-")
    cible = Path(tempo.name) / "source"
    resultat = subprocess.run(["git", "clone", "--depth", "1", "--quiet", depuis, str(cible)],
                              capture_output=True, text=True, timeout=180)
    if resultat.returncode != 0:
        tempo.cleanup()
        raise SystemExit(f"✗ Clonage impossible de {depuis} :\n{resultat.stderr.strip()}")
    return cible, tempo


def fichiers_methode(source: Path) -> dict[Path, Path]:
    """Associe chaque fichier de la méthode à son chemin dans le projet."""
    plan: dict[Path, Path] = {}

    for dossier in sorted((source / "skills").iterdir()):
        if not dossier.is_dir():
            continue
        if dossier.name.startswith(PREFIXE_PROJET):
            raise SystemExit(f"✗ Le skill de méthode « {dossier.name} » utilise le préfixe réservé "
                             f"aux projets ({PREFIXE_PROJET}). Renommez-le dans decupler-seo.")
        for f in dossier.rglob("*"):
            if f.is_file():
                plan[Path(".claude/skills") / dossier.name / f.relative_to(dossier)] = f

    for type_ in ("agents", "commands"):
        for f in sorted((source / type_).glob("*.md")):
            plan[Path(".claude") / type_ / f.name] = f

    for ressource in RESSOURCES:
        base = source / ressource
        if base.is_dir():
            for f in base.rglob("*"):
                if f.is_file() and "__pycache__" not in f.parts:
                    plan[DOSSIER_EMBARQUE / ressource / f.relative_to(base)] = f

    plugin_json = source / ".claude-plugin" / "plugin.json"
    if plugin_json.is_file():
        plan[DOSSIER_EMBARQUE / "plugin.json"] = plugin_json
    return plan


def ecrire(source: Path, cible: Path) -> None:
    """Copie un fichier ; dans le Markdown, repointe les scripts vers la copie embarquée."""
    cible.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix == ".md":
        texte = source.read_text(encoding="utf-8")
        # Chemin relatif à la racine du projet : c'est de là que Claude
        # travaille, en local comme dans une routine.
        cible.write_text(texte.replace(JETON, str(DOSSIER_EMBARQUE)), encoding="utf-8")
    else:
        shutil.copy2(source, cible)


def lire_manifeste(projet: Path) -> dict:
    chemin = projet / MANIFESTE
    if not chemin.is_file():
        return {"version": None, "fichiers": {}}
    return json.loads(chemin.read_text(encoding="utf-8"))


# ─── Synchronisation ──────────────────────────────────────────────

def synchroniser(projet: Path, source: Path, forcer: bool = False, simuler: bool = False) -> int:
    ancien = lire_manifeste(projet)
    plan = fichiers_methode(source)
    version = version_de(source)

    # 1. Repérer les fichiers de méthode modifiés à la main dans le projet.
    modifies = []
    for rel, empreinte_connue in ancien["fichiers"].items():
        chemin = projet / rel
        if chemin.is_file() and empreinte(chemin) != empreinte_connue:
            modifies.append(rel)

    if modifies and not forcer:
        print(f"\n✗ {len(modifies)} fichier(s) de méthode modifié(s) localement dans ce projet :\n")
        for rel in modifies[:20]:
            print(f"    {rel}")
        print("\n  Une synchronisation les écraserait. Deux options :")
        print("  · la modification est une amélioration de méthode → reportez-la dans")
        print("    decupler-seo, pour que tous les projets en profitent, puis resynchronisez ;")
        print("  · la modification est propre à ce client → déplacez-la dans un skill")
        print(f"    .claude/skills/{PREFIXE_PROJET}…, que la synchronisation ne touche jamais.")
        print("\n  Relancez avec --forcer une fois ce choix fait.\n")
        return 1

    # 2. Calculer ce qui change.
    ajoutes, maj, inchanges = [], [], []
    for rel, src in plan.items():
        cible = projet / rel
        if not cible.exists():
            ajoutes.append(rel)
        else:
            tempo = Path(tempfile.mkstemp()[1])
            ecrire(src, tempo)
            (inchanges if empreinte(tempo) == empreinte(cible) else maj).append(rel)
            tempo.unlink()
    nouveaux = {str(r) for r in plan}
    retires = [Path(r) for r in ancien["fichiers"] if r not in nouveaux]

    print(f"\n  Méthode {ancien['version'] or '(aucune)'} → {version}")
    print(f"  {len(ajoutes)} ajouté(s) · {len(maj)} mis à jour · {len(retires)} retiré(s) · "
          f"{len(inchanges)} inchangé(s)")
    if simuler:
        for libelle, lot in (("+", ajoutes), ("~", maj), ("-", retires)):
            for rel in lot[:30]:
                print(f"    {libelle} {rel}")
        print("\n  Simulation : rien n'a été écrit.\n")
        return 0

    # 3. Appliquer.
    for rel in ajoutes + maj:
        ecrire(plan[rel], projet / rel)
    for rel in retires:
        chemin = projet / rel
        if chemin.is_file():
            chemin.unlink()
            # Nettoyer les dossiers de skill devenus vides.
            parent = chemin.parent
            while parent != projet and parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent

    manifeste = {
        "version": version,
        "synchronise_le": dt.datetime.now().isoformat(timespec="seconds"),
        "fichiers": {str(rel): empreinte(projet / rel) for rel in plan},
    }
    (projet / MANIFESTE).parent.mkdir(parents=True, exist_ok=True)
    (projet / MANIFESTE).write_text(json.dumps(manifeste, ensure_ascii=False, indent=1), encoding="utf-8")
    (projet / DOSSIER_EMBARQUE / "VERSION").write_text(version + "\n", encoding="utf-8")

    print(f"  ✓ Méthode synchronisée dans {projet / '.claude'}\n")
    return 0


# ─── Création d'un projet ─────────────────────────────────────────

def remplir(texte: str, valeurs: dict[str, str]) -> str:
    for cle, valeur in valeurs.items():
        texte = texte.replace("{{" + cle + "}}", valeur)
    return texte


def initialiser(args) -> int:
    projet = Path(args.dossier).expanduser().resolve()
    if projet.exists() and any(p for p in projet.iterdir() if p.name != ".git"):
        if (projet / "CLAUDE.md").exists() and not args.forcer:
            print(f"✗ {projet} contient déjà un CLAUDE.md. Utilisez `sync` pour mettre à jour "
                  "la méthode, ou --forcer pour réinitialiser le gabarit.")
            return 1

    domaine = args.domaine.rstrip("/")
    if "//" not in domaine:
        domaine = "https://" + domaine
    domaine_nu = urlparse(domaine).netloc.removeprefix("www.")
    langues = [l.strip() for l in args.langues.split(",") if l.strip()]

    valeurs = {
        "NOM": args.nom,
        "DOMAINE": domaine,
        "DOMAINE_NU": domaine_nu,
        "PAYS": args.pays,
        "LANGUES": ", ".join(langues),
        "LANGUES_YAML": ", ".join(langues),
        "LANGUE_PRINCIPALE": langues[0] if langues else "fr",
        "CMS": args.cms,
        "ACTIVITE": args.activite,
        "PROPOSITION_VALEUR": args.proposition,
        "TON": args.ton,
        "VOUVOIEMENT": "true" if args.vouvoiement else "false",
        "PAGES_MAX": str(args.pages_max),
        "MODE": args.mode,
        "PUBLICATION": args.publication,
        "DATE": dt.date.today().isoformat(),
        "PAR": args.par,
    }

    source, tempo = obtenir_source(args.depuis)
    try:
        modele = source / MODELE
        if not modele.is_dir():
            print(f"✗ Gabarit introuvable : {modele}")
            return 1

        projet.mkdir(parents=True, exist_ok=True)
        for f in modele.rglob("*"):
            if not f.is_file():
                continue
            cible = projet / f.relative_to(modele)
            if cible.exists() and not args.forcer:
                continue
            cible.parent.mkdir(parents=True, exist_ok=True)
            try:
                cible.write_text(remplir(f.read_text(encoding="utf-8"), valeurs), encoding="utf-8")
            except UnicodeDecodeError:
                shutil.copy2(f, cible)

        # Le .mcp.json vit à la racine du projet : c'est là qu'une routine le lit.
        # Il appartient ensuite au projet, qui peut retirer les serveurs inutiles.
        mcp = projet / ".mcp.json"
        if not mcp.exists() and (source / ".mcp.json").is_file():
            shutil.copy2(source / ".mcp.json", mcp)

        restants = sorted({m for f in projet.rglob("*") if f.is_file() and ".git" not in f.parts
                           and f.suffix in {".md", ".yml", ".example"}
                           for m in re.findall(r"\{\{([A-Z_]+)\}\}", f.read_text(encoding="utf-8",
                                                                                 errors="ignore"))})
        print(f"\n  ✓ Projet « {args.nom} » créé dans {projet}")
        code = synchroniser(projet, source, forcer=True)
    finally:
        if tempo:
            tempo.cleanup()

    if restants:
        print(f"  ! Champs encore à remplir : {', '.join(restants)}")
    print("  Prochaines étapes :")
    print("    1. Compléter memoire/marque.md — c'est lui qui rend le contenu propre à ce client")
    print("    2. git init && créer le dépôt PRIVÉ sur GitHub, puis pousser")
    print("    3. Créer les 4 routines décrites dans ROUTINES.md\n")
    return code


# ─── Statut ───────────────────────────────────────────────────────

def statut(args) -> int:
    projet = Path(args.dossier).expanduser().resolve()
    manifeste = lire_manifeste(projet)
    if not manifeste["version"]:
        print(f"\n  Aucune méthode synchronisée dans {projet}.")
        print(f"  → python3 {Path(__file__).name} sync {args.dossier}\n")
        return 1

    modifies = [rel for rel, e in manifeste["fichiers"].items()
                if (projet / rel).is_file() and empreinte(projet / rel) != e]
    manquants = [rel for rel in manifeste["fichiers"] if not (projet / rel).is_file()]
    propres = sorted(p.name for p in (projet / ".claude" / "skills").glob(f"{PREFIXE_PROJET}*") if p.is_dir())

    print(f"\n  Projet    : {projet}")
    print(f"  Méthode   : {manifeste['version']}  (synchronisée le {manifeste.get('synchronise_le', '?')})")
    print(f"  Fichiers  : {len(manifeste['fichiers'])} gérés par la méthode")
    print(f"  Skills propres au projet : {', '.join(propres) or 'aucun'}")
    if modifies:
        print(f"  ! {len(modifies)} fichier(s) de méthode modifié(s) localement :")
        for rel in modifies[:10]:
            print(f"      {rel}")
    if manquants:
        print(f"  ! {len(manquants)} fichier(s) de méthode supprimé(s) localement")

    source_version = version_de(RACINE_METHODE)
    if source_version != manifeste["version"]:
        print(f"  → Une autre version est disponible ici : {source_version}")
    print()
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Projets decupler-seo")
    sp = p.add_subparsers(dest="commande", required=True)

    i = sp.add_parser("init", help="créer un projet à partir du gabarit")
    i.add_argument("dossier")
    i.add_argument("--nom", required=True)
    i.add_argument("--domaine", required=True)
    i.add_argument("--pays", default="FR")
    i.add_argument("--langues", default="fr", help="ex. fr ou ar,en")
    i.add_argument("--cms", default="wordpress")
    i.add_argument("--publication", default="cms", choices=["cms", "depot"],
                   help="depot pour un site en code : publier = fusionner une PR")
    i.add_argument("--activite", default="")
    i.add_argument("--proposition", default="")
    i.add_argument("--ton", default="expert, direct, sans jargon inutile")
    i.add_argument("--vouvoiement", action=argparse.BooleanOptionalAction, default=True)
    i.add_argument("--pages-max", type=int, default=3)
    i.add_argument("--mode", default="assisted", choices=["safe", "assisted", "autonomous"],
                   help="assisted par défaut : un nouveau projet commence sous surveillance")
    i.add_argument("--par", default="")
    i.add_argument("--depuis", help="dossier ou URL git de decupler-seo")
    i.add_argument("--forcer", action="store_true")

    s = sp.add_parser("sync", help="installer ou mettre à jour la méthode dans un projet")
    s.add_argument("dossier")
    s.add_argument("--depuis", help="dossier ou URL git de decupler-seo")
    s.add_argument("--forcer", action="store_true", help="écraser les modifications locales")
    s.add_argument("--simuler", action="store_true", help="montrer sans écrire")

    t = sp.add_parser("statut", help="version et intégrité de la méthode embarquée")
    t.add_argument("dossier")

    args = p.parse_args()
    if args.commande == "init":
        return initialiser(args)
    if args.commande == "sync":
        projet = Path(args.dossier).expanduser().resolve()
        source, tempo = obtenir_source(args.depuis)
        try:
            return synchroniser(projet, source, forcer=args.forcer, simuler=args.simuler)
        finally:
            if tempo:
                tempo.cleanup()
    return statut(args)


if __name__ == "__main__":
    sys.exit(main())
