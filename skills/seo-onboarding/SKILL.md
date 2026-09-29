---
name: seo-onboarding
description: >
  Point d'entrée de Claude Code SEO Décupler. Accueille un nouvel utilisateur,
  diagnostique ce qui est branché, explique quoi connecter en premier et
  pourquoi, configure le projet, puis lance la première action utile.
  Déclencher quand l'utilisateur dit "je commence", "installe", "configure",
  "par où je commence", "qu'est-ce que je dois connecter", "ça marche pas",
  "doctor", "quels outils", ou à la toute première utilisation du dispositif
  sur un projet (aucun decupler-seo.config.yml dans le dossier du projet).
---

# Onboarding — la première demi-heure

Votre travail ici : faire passer quelqu'un de « j'ai cloné un repo » à
« j'ai un premier livrable SEO exploitable », sans qu'il ait à lire la doc.

Règle absolue de ce skill : **ne jamais bloquer sur un outil manquant.**
Il y a toujours quelque chose d'utile à faire avec ce qui est déjà là.

## 1. Diagnostiquer avant de parler

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py" --json
```

Lisez le résultat avant d'ouvrir la bouche. Vous saurez : les prérequis
système, quels outils répondent, ce qui manque, et le coût de chaque
branchement.

## 2. Dire où on en est, en trois lignes

Pas de mur de texte. Le format :

> Vous avez **X outils sur 13** branchés.
> Avec ça, vous pouvez déjà : [2-3 actions concrètes].
> Le prochain branchement le plus rentable : **[outil]** — [gratuit/payant],
> [temps d'installation], et ça débloque [bénéfice précis].

## 3. L'ordre de branchement (ne pas improviser)

L'ordre compte. Il est calculé sur le rapport valeur/effort, pas sur la
notoriété des outils.

| # | Outil | Coût | Temps | Ce que ça débloque |
|---|-------|------|-------|--------------------|
| 1 | **Search Console** | gratuit | 10 min | Tout le pipeline de priorisation. Sans lui, vous devinez. |
| 2 | **Chrome DevTools** | gratuit | 0 min | Core Web Vitals réels, rendu final, screenshots. |
| 3 | **GA4** | gratuit | 10 min | Relie le SEO au chiffre d'affaires. |
| 4 | **Firecrawl** | gratuit (offre) | 2 min | Lecture propre des concurrents. |
| 5 | **DataForSEO** | à la requête | 5 min | Volumes et SERP live. Le moins cher du marché. |
| 6 | **Notion** | gratuit | 1 clic | Pilotage : leads, objectifs, roadmap. |
| 7 | **WordPress / Webflow** | gratuit | 5 min | Publication automatique. |
| 8+ | Ahrefs, Semrush, Perplexity, Reddit, Ubersuggest | variable | — | Backlinks, gaps, visibilité IA. |

**Les 4 premiers sont gratuits et couvrent 70 % de la valeur.** Dites-le.
Beaucoup de gens croient qu'il faut 500 €/mois d'outils pour commencer.

## 4. Connecter Search Console — la seule étape qui mérite du détail

Deux chemins, à proposer selon le profil :

**Chemin A — connecteur (5 min, aucun code).** Réglages Claude →
Connecteurs → autoriser l'accès Google → sélectionner la propriété.
Pour quelqu'un qui ne veut pas voir un terminal.

**Chemin B — compte de service (10 min, accès complet, scriptable).**

1. Google Cloud Console → nouveau projet
2. Activer l'API **Search Console**
3. IAM → Comptes de service → créer → générer une clé JSON
4. Déposer le fichier dans `./secrets/gsc-service-account.json`
5. Search Console → Paramètres → Utilisateurs → ajouter l'email du compte
   de service **en lecture seule**
6. Dans `.env` :
   ```
   GSC_SITE_URL=https://votre-site.com/
   GSC_CREDENTIALS_JSON=./secrets/gsc-service-account.json
   ```

⚠️ Ne donnez jamais le rôle **propriétaire** à un compte de service. Lecture
seule suffit pour tout ce que fait ce dispositif.

À signaler : l'API Search Console ne remonte que **16 mois** d'historique.
Si vous voulez des comparaisons annuelles au-delà, il faut archiver.

## 5. Remplir la fiche projet

La configuration appartient au **projet**, pas au plugin : le dossier du plugin
est remplacé à chaque mise à jour, et un fichier modifié là-bas serait perdu.

Si le projet n'a pas encore de config, créez-la à la racine du projet :

```bash
cp "${CLAUDE_PLUGIN_ROOT}/config/decupler-seo.config.yml" ./decupler-seo.config.yml
cp "${CLAUDE_PLUGIN_ROOT}/config/.env.example" ./.env
```

Vérifiez que `.env` est dans le `.gitignore` du projet avant d'y mettre une clé.
Puis remplissez la section `projet` de `./decupler-seo.config.yml`.
Un dossier par site ou par client = une config et un `.env` par site ou par client.
Posez les questions en une seule fois, pas une par une :

- Le domaine ?
- Ce que vous vendez, en une phrase ?
- Vos 3 concurrents SEO (ceux qui sortent sur vos requêtes, pas vos
  concurrents commerciaux — ce n'est souvent pas la même liste) ?
- Les 3-5 pages qui doivent générer du chiffre ?
- Vouvoiement ou tutoiement ?

Ces réponses évitent de reposer les mêmes questions à chaque session. Un
utilisateur qui les donne une fois gagne 5 minutes par run ensuite.

## 6. Expliquer le kill-switch, en une phrase

> Par défaut le dispositif est en mode **autonomous** : il écrit tout seul.
> Trois façons de l'arrêter : dites « passe en safe mode », ajoutez `--safe`
> à une commande, ou mettez `SEO_SAFE_MODE=1` dans `.env`.
> Quoi qu'il arrive, il ne supprimera jamais de contenu et ne postera jamais
> sur un forum ou par email sans votre accord explicite.

## 7. Lancer la première action — ne pas laisser en plan

Ne terminez jamais l'onboarding sur « voilà, à vous ». Proposez et exécutez
la première action, choisie selon ce qui est branché :

| Ce qui est branché | Première action |
|--------------------|-----------------|
| Search Console | `/seo quickwins` — les positions 8-20 à rattraper. Effet immédiat. |
| Rien, mais une URL | `/seo audit <url>` — audit technique + contenu sans aucune clé. |
| Un texte collé | `/seo onpage` — score /100 et réécriture. |
| Notion | `/seo notion setup` — les 5 bases de pilotage. |

## 8. Quand quelque chose ne marche pas

| Symptôme | Cause la plus fréquente | Correctif |
|----------|------------------------|-----------|
| MCP absent de la liste | Node manquant, ou Claude non redémarré | `node -v`, puis relancer Claude Code |
| GSC renvoie 403 | Compte de service pas ajouté dans Search Console | Ajouter l'email en lecture seule |
| GSC renvoie 0 ligne | Mauvais format de propriété | Essayer `sc-domain:exemple.com` |
| DataForSEO 401 | Login/mot de passe API ≠ identifiants du site | Les récupérer dans API Access |
| WordPress 401 | Mot de passe de compte au lieu du mot de passe d'application | En générer un dans Profil |
| Chrome DevTools ne rend rien | Chrome absent | Installer Chrome ou Chromium |

Plus de cas dans `docs/DEPANNAGE.md`.

## Sortie attendue

Un message court, une action lancée, et le sentiment que ça marche. Pas un
tutoriel. Si vous avez écrit plus de 400 mots sans rien exécuter, vous vous
êtes trompé.
