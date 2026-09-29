---
name: seo-nouveau-projet
description: >
  Crée un nouveau projet SEO piloté en autonomie : dépôt privé à partir du
  gabarit, mémoire du projet (CLAUDE.md, marque, décisions, apprentissages),
  méthode embarquée pour les routines, configuration, et les quatre routines
  prêtes à créer. Déclencher sur "nouveau projet", "nouveau client", "lancer
  un site", "onboarder un client", "créer le repo du projet", "mettre un
  client sous pilotage", "ajouter un site au portefeuille".
---

# Nouveau projet

Un projet = un dépôt **privé**. Il contient ce qui est propre au client
(mémoire, config, journal, données) et une copie de la méthode decupler-seo
dans `.claude/` — c'est la seule façon pour une routine cloud de l'utiliser,
car elle ne charge pas les plugins installés via marketplace.

## 1. Tout demander en une fois

Une seule liste de questions, pas un interrogatoire en dix messages :

**Identité**
- Nom du projet, domaine (existant ou à créer)
- Activité, en une phrase : ce qui est vendu, à qui
- Les 3-5 pages ou offres qui doivent rapporter

**Marché**
- Pays, langue(s) de rédaction, langue principale
- Les 3 concurrents qui sortent sur les requêtes visées

**Technique**
- CMS (WordPress, Webflow, Contentful, Shopify, statique, à créer)
- Accès : Search Console, GA4, API du CMS — lesquels sont déjà disponibles ?

**Marque**
- Ton, vouvoiement ou tutoiement
- Chiffres officiels utilisables, preuves (clients, certifications, presse)
- Ce qui est interdit (promesses, termes, sujets)

**Pilotage**
- Mode de départ : `assisted` recommandé les 3-4 premières semaines, puis
  `autonomous` une fois que les premières mesures sont bonnes
- Plafond de pages neuves par semaine (3 par défaut)
- Règle d'occurrences du mot-clé propre à ce client, s'il y en a une

Ce qu'on ne sait pas encore reste vide : mieux vaut un champ vide qu'une
supposition qui finira dans un contenu publié.

## 2. Créer le projet

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/projet.py" init ../<slug-projet> \
  --nom "<Nom>" --domaine <https://domaine> --pays <XX> --langues <fr|ar,en|…> \
  --cms <cms> --activite "<activité>" --proposition "<proposition de valeur>" \
  --mode assisted --pages-max 3 --par "<qui lance le projet>"
```

Puis compléter `memoire/marque.md` avec les réponses : voix, lexique,
chiffres officiels **avec leur source**, interdits, preuves. C'est le
fichier qui fait la différence entre un contenu du client et un contenu
générique — il mérite dix minutes.

Si le site a déjà des pages écrites par le client, mesurer son style dans
la foulée (5 à 10 pages), puis remplir la section « Lecture » :

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/style_maison.py" <url1> <url2> …
```

## 3. Le dépôt privé

```bash
cd ../<slug-projet>
git init -b main && git add -A && git commit -m "Création du projet <Nom>"
```

Créer le dépôt **privé** sur GitHub (`gh repo create <compte>/<slug> --private
--source . --push` si `gh` est disponible, sinon github.com/new puis
`git remote add origin … && git push -u origin main`).

Vérifier avant le premier push que `.env` n'est pas suivi :
`git ls-files | grep -E '\.env$'` ne doit rien renvoyer.

## 4. Les routines

Suivre `ROUTINES.md`, généré dans le projet : quatre routines, un
environnement cloud dédié dont le réseau autorise le domaine du projet, et
uniquement les connecteurs utiles.

Si c'est l'agent qui les crée (outil `create_trigger`), il ne peut pas leur
donner de dépôt : une session neuve sans dépôt se termine sans rien faire,
avec un statut « réussi ». Procédure qui marche :
1. `create_session` avec `source_url` = le dépôt du projet, et une première
   consigne de vérification (méthode, Search Console, accès au site, push) ;
2. `create_trigger` avec `persistent_session_id` = cette session, une
   routine par mode, chaque consigne commençant par
   `git fetch origin && git checkout main && git pull --ff-only` et finissant
   par « ne fusionne jamais dans main » sur un site en mode `depot` ;
3. vérifier après la première exécution planifiée qu'une branche
   `claude/veille-<date>` est bien apparue sur le dépôt. Pas de branche = la
   routine ne marche pas, quel que soit son statut : la recréer depuis
   claude.ai/code/routines en choisissant le dépôt. (Un déclenchement
   manuel par `fire_trigger` ouvre une session neuve sans dépôt : il ne
   teste pas ce montage.)

## 5. La première semaine

Avant d'automatiser quoi que ce soit, établir le point de départ :

1. `seo-audit-360` — l'état des lieux, archivé dans `rapports/`
2. Un premier instantané Search Console dans `donnees/`
3. `seo-technique-autofix` en mode proposition : les blocages techniques
   d'abord, sinon tout le reste est inutile
4. Le lexique du métier dans `memoire/lexique.csv`, validé avec le client
   (thèmes et valeur 1 à 3), puis le premier classement `seo-opportunites`
5. Consigner dans `memoire/decisions.md` ce qui est validé ou refusé

## Projet dans un autre pays ou une autre langue

Ce qu'il faut trancher dès la création, parce que ça ne se corrige pas
facilement ensuite :

- **Architecture multilingue** : sous-dossiers par langue par défaut, avec
  hreflang et x-default — voir `seo-hreflang-i18n`. À décider avant la
  première page publiée.
- **Recherche de mots-clés dans la langue et le pays cibles**, avec la bonne
  localisation dans DataForSEO, Semrush ou Ubersuggest. Traduire une liste
  de mots-clés français ne donne pas les requêtes réelles du marché.
- **Rédaction native**, pas traduction : les requêtes, les objections et les
  preuves attendues diffèrent d'un marché à l'autre.
- **Mise en page** : si une langue s'écrit de droite à gauche, les gabarits
  HTML doivent déclarer `dir` et `lang` et être vérifiés dans ce sens.
- **Preuves locales** : références, adresses, certifications et mentions
  légales du pays visé. Ce qui rassure en France ne rassure pas forcément
  ailleurs.
- **Moteurs et usages** : vérifier sur des SERP réelles du pays quels
  formats et quels acteurs dominent, plutôt que de le supposer.

## Mettre à jour la méthode d'un projet existant

```bash
python3 .claude/decupler-seo/scripts/projet.py sync .
python3 .claude/decupler-seo/scripts/projet.py statut .
```

La synchronisation refuse d'écraser un fichier de méthode modifié à la main
dans le projet, et dit pourquoi : une amélioration de méthode remonte dans
decupler-seo, une règle propre au client va dans un skill `projet-…`.
