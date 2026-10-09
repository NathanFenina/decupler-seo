#!/usr/bin/env python3
"""Diagnostic d'installation — dit ce qui est branché et ce qui manque.

    python3 scripts/doctor.py           # rapport lisible
    python3 scripts/doctor.py --json    # sortie machine, pour les skills

Le principe : on ne bloque jamais l'utilisateur parce qu'un outil manque.
On lui dit ce qu'il peut faire dès maintenant, ce qu'il débloque en
branchant tel outil, et combien ça lui coûte.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import charger_env, config_est_le_modele, fichier_config, racine_projet, resoudre  # noqa: E402

# (identifiant, nom, variables requises, niveau, ce que ça débloque, où l'obtenir, coût)
OUTILS = [
    ("search-console", "Google Search Console", ["GSC_SA_JSON|GSC_CREDENTIALS_JSON"], 1,
     "Quick wins, rapports, diagnostic de chute de trafic, priorisation réelle",
     "Google Cloud → Search Console API → compte de service, ou votre compte : "
     "gcloud auth application-default login (voir gsc.py)", "gratuit"),
    ("google-analytics", "Google Analytics 4", ["GA4_PROPERTY_ID", "GA4_CREDENTIALS_JSON"], 1,
     "Conversions organiques, valeur business par page, rapport mensuel complet",
     "Google Cloud → Analytics Data API → compte de service", "gratuit"),
    ("chrome-devtools", "Chrome DevTools", [], 1,
     "Core Web Vitals mesurés, rendu réel, screenshots, audit technique fiable",
     "Rien à faire — nécessite Node et Chrome", "gratuit"),
    ("firecrawl", "Firecrawl", ["FIRECRAWL_API_KEY"], 2,
     "Lecture propre des concurrents, extraction de plans Hn, veille",
     "https://firecrawl.dev", "offre gratuite généreuse"),
    ("dataforseo", "DataForSEO", ["DATAFORSEO_LOGIN|DATAFORSEO_USERNAME", "DATAFORSEO_PASSWORD"], 2,
     "Volumes de recherche, difficulté, SERP live, positions concurrents",
     "https://app.dataforseo.com/api-access", "à la requête, ~0,05 $ / appel"),
    ("treg", "Treg (routeur d'outils)", ["TREG_TOKEN"], 2,
     "Un jeton, 3 800 points d'accès payés à l'appel : mots-clés, SERP, backlinks, visibilité IA",
     "https://treg.to", "à l'appel, au prix du fournisseur"),
    ("ubersuggest", "Ubersuggest", ["UBERSUGGEST_API_KEY"], 2,
     "Expansion sémantique, suggestions Google, idées de contenu",
     "Connecteur claude.ai (un clic, sans clé) ou clé API", "abonnement ou connecteur"),
    ("semrush", "Semrush", ["SEMRUSH_API_KEY"], 3,
     "Gaps de mots-clés concurrents, position tracking",
     "https://www.semrush.com/api-analytics/", "plan API requis"),
    ("ahrefs", "Ahrefs", ["AHREFS_API_KEY"], 3,
     "Backlinks, autorité, prospection netlinking chiffrée",
     "https://ahrefs.com/api", "plan API requis"),
    ("wordpress", "WordPress (facultatif)", ["WP_SITE_URL", "WP_USER|WP_USERNAME", "WP_APP_PASSWORD"], 3,
     "Publication en brouillon, title/meta journalisés, carte de contenu et maillage (wp.py)",
     "WordPress → Profil → Mots de passe d'application", "gratuit"),
    ("webflow", "Webflow", ["WEBFLOW_TOKEN", "WEBFLOW_SITE_ID"], 3,
     "Création et mise à jour d'items CMS, publication",
     "Webflow → Site settings → API access", "gratuit"),
    ("notion", "Notion", ["NOTION_TOKEN"], 3,
     "Pilotage : leads, objectifs, roadmap, briefs, backlinks",
     "Connecteur claude.ai natif (recommandé) ou clé d'intégration", "gratuit"),
    ("openai", "OpenAI (ChatGPT)", ["OPENAI_API_KEY"], 4,
     "Part de voix dans ChatGPT, sources citées (share_of_model.py)",
     "https://platform.openai.com/api-keys", "quelques centimes par mesure"),
    ("gemini", "Gemini", ["GEMINI_API_KEY"], 4,
     "Part de voix dans Gemini avec Google Search, proche des AI Overviews",
     "https://aistudio.google.com/apikey", "offre gratuite suffisante"),
    ("perplexity", "Perplexity (facultatif)", ["PERPLEXITY_API_KEY"], 4,
     "Part de voix dans Perplexity — utile seulement si votre audience l'utilise",
     "https://docs.perplexity.ai", "à l'usage, quelques euros / mois"),
    ("pangram", "Pangram (facultatif)", ["PANGRAM_API_KEY"], 3,
     "Détecteur d'IA en fin de passe d'humanisation, passages à reprendre (pangram.py)",
     "https://www.pangram.com → tableau de bord → API", "≈ 0,05 $ / 100 mots"),
    ("reddit", "Reddit", ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"], 4,
     "Questions réelles de l'audience, threads fortement cités par les LLM",
     "https://www.reddit.com/prefs/apps", "gratuit"),
]

ENV_LUS: list = []

NIVEAUX = {
    1: "Socle gratuit — commencez par là",
    2: "Donnée marché — débloque la stratégie",
    3: "Production et pilotage",
    4: "Visibilité IA (GEO)",
}



def _verifier(outil) -> dict:
    ident, nom, variables, niveau, debloque, obtenir, cout = outil
    manquantes = []
    for var in variables:
        if "|" in var:
            # Plusieurs variables possibles : une seule suffit.
            options = var.split("|")
            if not any(os.environ.get(o, "").strip() for o in options):
                manquantes.append(" ou ".join(options))
            continue
        valeur = os.environ.get(var, "").strip()
        if not valeur:
            manquantes.append(var)
        elif var.endswith("_JSON") and not resoudre(valeur).exists():
            manquantes.append(f"{var} (fichier introuvable : {valeur})")
    return {
        "id": ident,
        "nom": nom,
        "niveau": niveau,
        "branche": not manquantes,
        "manquantes": manquantes,
        "debloque": debloque,
        "obtenir": obtenir,
        "cout": cout,
    }


def diagnostic() -> dict:
    global ENV_LUS
    ENV_LUS = charger_env()
    resultats = [_verifier(o) for o in OUTILS]
    branches = [r for r in resultats if r["branche"]]
    prerequis = {
        "python3": sys.version.split()[0],
        "node": "présent" if shutil.which("node") else "absent — requis pour les MCP en npx",
        "git": "présent" if shutil.which("git") else "absent",
        "chrome": "présent" if any(
            shutil.which(b) for b in ("google-chrome", "chromium", "chromium-browser")
        ) else "non détecté — Chrome DevTools MCP en sera limité",
    }
    return {
        "outils": resultats,
        "branches": len(branches),
        "total": len(resultats),
        "prerequis": prerequis,
        "config": str(fichier_config()) if fichier_config() else None,
        "config_est_le_modele": config_est_le_modele(),
        "env_lus": [str(f) for f in ENV_LUS],
        "projet": str(racine_projet()),
    }


def afficher(rapport: dict) -> None:
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║  Claude Code SEO Décupler — diagnostic                       ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    print("Prérequis système")
    for cle, valeur in rapport["prerequis"].items():
        marque = "✓" if "absent" not in valeur and "non détecté" not in valeur else "!"
        print(f"  {marque} {cle:<10} {valeur}")

    print(f"\n  Projet : {rapport['projet']}")
    if not rapport["env_lus"]:
        print("  ! Aucun fichier .env dans ce projet.")
        print("    → créez-en un à partir de config/.env.example du plugin.")
    if rapport["config_est_le_modele"] or not rapport["config"]:
        print("  ! Aucune config propre à ce projet — le modèle par défaut s'applique.")
        print("    → copiez-le en ./decupler-seo.config.yml et remplissez la section projet.")

    for niveau in sorted(NIVEAUX):
        outils = [o for o in rapport["outils"] if o["niveau"] == niveau]
        if not outils:
            continue
        print(f"\n─── Niveau {niveau} · {NIVEAUX[niveau]} " + "─" * max(0, 24 - len(NIVEAUX[niveau])))
        for o in outils:
            if o["branche"]:
                print(f"  ✓ {o['nom']}")
            else:
                print(f"  ○ {o['nom']}  ({o['cout']})")
                print(f"      débloque : {o['debloque']}")
                print(f"      obtenir  : {o['obtenir']}")
                if o["manquantes"]:
                    print(f"      manque   : {', '.join(o['manquantes'])}")

    print(f"\n{rapport['branches']}/{rapport['total']} outils branchés.\n")

    manquants_n1 = [o for o in rapport["outils"] if o["niveau"] == 1 and not o["branche"]]
    if manquants_n1:
        print("Prochaine étape la plus rentable :")
        print(f"  Branchez {manquants_n1[0]['nom']} — c'est gratuit et ça débloque")
        print(f"  {manquants_n1[0]['debloque'].lower()}.")
        print(f"  → {manquants_n1[0]['obtenir']}\n")
    elif rapport["branches"] >= 4:
        print("Vous avez de quoi travailler sérieusement. Lancez :")
        print("  /seo audit https://votre-site.com\n")
    print("Détail complet des branchements : docs/MCP.md\n")


def main() -> int:
    parseur = argparse.ArgumentParser(description="Diagnostic Claude Code SEO Décupler")
    parseur.add_argument("--json", action="store_true", help="sortie JSON")
    args = parseur.parse_args()
    rapport = diagnostic()
    if args.json:
        print(json.dumps(rapport, ensure_ascii=False, indent=2))
    else:
        afficher(rapport)
    return 0


if __name__ == "__main__":
    sys.exit(main())
