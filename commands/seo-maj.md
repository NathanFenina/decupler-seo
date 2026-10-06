---
description: Mettre à jour la méthode decupler-seo (plugin et projet en cours), et renvoyer vers la méthode une amélioration faite ici
---
Selon l'endroit où on se trouve, faites dans l'ordre ce qui s'applique, en
expliquant chaque étape en une ligne.

## 1. Ce que la méthode a de nouveau

`python3 .claude/decupler-seo/scripts/projet.py statut .` dans un projet (ou
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/projet.py" statut .`). Il dit la
version embarquée, les fichiers de méthode modifiés à la main, et si une
version plus récente est publiée.

## 2. D'abord, ne rien perdre

Si des fichiers de méthode ont été modifiés dans ce projet, demandez pour
chacun : amélioration valable pour tous les sites, ou adaptation propre à
ce client ?
- pour tous → `python3 .claude/decupler-seo/scripts/projet.py remonter . [fichiers] --pousser`
  (branche `remontee/…` sur decupler-seo, puis ouvrir la pull request) ;
- propre au client → déplacer le contenu dans un skill `.claude/skills/projet-…`
  et remettre le fichier de méthode d'origine.

Ne jamais lancer `sync --forcer` tant que ce tri n'est pas fait.

## 3. Mettre le projet à jour

Sur une branche `methode/decupler-seo-<version>` :
1. `python3 .claude/decupler-seo/scripts/projet.py sync .`
2. `python3 .claude/decupler-seo/scripts/projet.py completer .` (nouveaux fichiers du
   gabarit : Obsidian, notes, routines… ; rien d'existant n'est remplacé)
3. les contrôles du projet (`controle.commandes` dans `decupler-seo.config.yml`)
4. commit, push, pull request. La fusion suit les règles du projet : sur un
   site où fusionner déploie, la PR attend un humain.

## 4. Mettre à jour le plugin sur ce poste (session locale seulement)

`claude plugin marketplace update decupler` puis
`claude plugin update decupler-seo@decupler`, et redémarrer la session pour
charger la nouvelle version. Pour ne plus y penser : `/plugin` → onglet
Marketplaces → `decupler` → activer la mise à jour automatique.

Une session cloud ou une routine ne charge pas le plugin : elle utilise la
copie embarquée dans le dépôt, mise à jour par l'étape 3 (ou par la PR
automatique du lundi, `.github/workflows/sync-methode.yml`).

Terminez par une ligne : version avant → après, PR ouvertes, et ce qui
attend une décision.
