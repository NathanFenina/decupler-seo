---
name: seo-pilotage
description: Tableau de bord partagé de plusieurs projets et leur roadmap validée par le client — propositions du mois, validation, exécution par les routines, statut « faite » avec le lien du résultat. Déclencher sur « roadmap », « tableau de bord », « actions à valider », « qu'est-ce qu'on lance », « lance les tâches validées », à l'ouverture de la conversation dédiée à un projet, et dans les routines de rapport, d'optimisation et de contenu.
---

# Pilotage — la roadmap validée

Chaque projet a **une seule** page de suivi publiée (Artifact) : roadmap,
avancement, chiffres, cartographie, liens vers les livrables. Toutes les
conversations et toutes les routines du projet passent par elle ; c'est ce qui
évite de faire deux fois la même chose quand on jongle entre les conversations. Son adresse est dans `decupler-seo.config.yml` (`pilotage.tableau_de_bord`),
l'identifiant du projet dans `pilotage.projet_id`. La page garde son état dans un
bloc JSON : chiffres, cartographie et **actions** de chaque projet. Le client y
clique « Valider » ou « Refuser » ; les routines n'exécutent que ce qui est validé.

Statuts d'une action : `proposee` → `validee` (ou `refusee`) → `en-cours` → `faite`,
et `bloquee` quand elle attend quelqu'un ou quelque chose (`--attend "la freelance"`,
`"accès FTP"`, `"réponse de Google"`) : elle remonte alors dans « À décider ».

Chaque action a un **chantier**, qui la range dans la page : `contenus`,
`optimisation`, `technique`, `off-page`, `geo`, `international`, `securite`,
`indexation`, `design`, `pilotage`.

## Un onglet par mois

La page montre un onglet par mois. Le mois en cours : **À décider** (à valider
et bloquées, avec boutons et remarque pour Claude), reporting, **Fait**, **À
faire** par chantier, **Wins**, **Contenus** (lien vers la page et vers
Notion), semaine par semaine, puis cartographie, livrables et routines. Les
mois passés gardent leur fait, leurs wins, leurs contenus et leur reporting.
Une action faite se range dans le mois de sa date (`maj`) ; pour reprendre un
historique : `ajouter --date AAAA-MM-JJ`.

Le bilan d'une semaine ou d'un mois s'écrit avec `pilotage.py mois --fichier
<json>` (format dans `routines/hebdo.md`) : relancé, il ne double rien. Le
lien de la base Notion des contenus va dans le projet (`notion`), celui de
chaque contenu dans sa ligne.

## Aux couleurs du projet

Chaque projet garde sa charte : `pilotage.py injecter --theme theme.json`, avec
les jetons du design system du client (`mode` sombre ou clair, `fond`, `carte`,
`encre`, `doux`, `trait`, `accent`, `accent_doux`, `cta`, `cta_texte`, `lien`,
`titre`, `texte`, `polices` = URL Google Fonts). En mode sombre, la page suit
la marque quel que soit le thème du lecteur. Vérifier les contrastes (texte
4,5:1, bouton `cta` / `cta_texte` compris) avant de publier.

## Rien ne se perd

- La page publiée garde ses versions, et un conflit d'enregistrement est
  signalé, jamais silencieux.
- Après chaque republication : `pilotage.py sauvegarder --html … --projet-id …`
  écrit la part du projet dans `journal/pilotage.json`, **commité** avec le reste.
- Page abîmée ou à recréer : `pilotage.py restaurer --html <page> --projet-id …`.

## Lire et écrire la page

1. `Artifact` action `read` avec l'adresse du tableau de bord ; enregistrer le
   HTML reçu tel quel dans `donnees/tableau-de-bord.html` (jamais commité : il
   contient les données de tous les projets).
2. `scripts/pilotage.py` travaille sur ce fichier (`etat`, `injecter`, `marquer`).
3. `Artifact` publish avec `url` = l'adresse du tableau de bord et `file_path` =
   ce fichier. Sans `capabilities` (la page garde les siennes). En cas de conflit
   (quelqu'un a validé entre-temps), repartir de la version renvoyée, refaire
   l'étape 2, republier une fois.

Ne jamais réécrire la page à la main : seul le bloc `etat` change.

## Règle anti-doublon — dans toute conversation du projet

- **Avant** de lancer une tâche : lire la page et vérifier qu'elle n'y est pas
  déjà `en-cours` ou `faite` ; si oui, le dire au lieu de refaire.
- **Après** toute tâche livrée, même hors roadmap (demandée en conversation) :
  `pilotage.py ajouter --projet-id <id> --titre "<ce qui a été fait>" --statut faite --lien <PR ou URL>`,
  puis republier. Une tâche décidée mais pas encore faite : `--statut validee`.
- **Une seule page par projet.** Si le projet a déjà une page interne (un
  suivi de chantiers, un journal), on y loge le tableau de bord plutôt que d'en
  créer une autre : `pilotage.py integrer --hote <page lue> --etat-depuis <suivi>
  --sortie hub.html`. Le contenu d'origine est conservé tel quel sous la roadmap
  (`<template id="hote">`) ; pour le mettre à jour ensuite, on modifie ce bloc,
  jamais le reste de la page.
- **Jamais dans une page lue par le client** (compte rendu partagé, rapport
  client) : la roadmap interne et ses boutons n'y ont pas leur place. On la
  garde dans une page interne et on relie les livrables client depuis elle.

## À l'ouverture de la conversation du projet

Montrer la roadmap du projet, sans rien lancer :
`python3 <scripts>/pilotage.py etat --html donnees/tableau-de-bord.html --projet-id <id>`
— à valider, validées (prêtes à lancer), en cours, faites ce mois-ci. Proposer de
lancer les actions validées ; lancer celles que l'utilisateur désigne.

## Routine hebdo — le mercredi (par défaut)

Elle fait tout en un passage : lire la page, exécuter les actions validées
(comme ci-dessous), écrire le bilan de la semaine (`mois`), republier,
sauvegarder. Le premier mercredi du mois, elle ajoute les propositions du mois
(comme la routine de rapport). Détail : `routines/hebdo.md`.

## Routine de rapport — le 1er du mois (ou premier mercredi au rythme hebdo)

Après `cartographie.py mensuel` et `rapport.py` :
```bash
python3 <scripts>/pilotage.py donnees --sortie donnees/pilotage.json
python3 <scripts>/pilotage.py proposer --mois <AAAA-MM> --projet-id <id> --sortie donnees/actions-<AAAA-MM>.json
python3 <scripts>/pilotage.py injecter --html donnees/tableau-de-bord.html --projet-id <id> \
  --donnees donnees/pilotage.json --actions donnees/actions-<AAAA-MM>.json
```
puis publier. `donnees/pilotage.json` et `donnees/actions-*.json` sont des
fichiers de travail ignorés par git, comme la copie de la page : ne pas les
commiter, ne pas les supprimer, ils sont réécrits le mois suivant. Au plus 8 actions par mois, dont au plus 3 décisions. Une action
refusée ne revient pas ; une décision prise n'est jamais écrasée.

## Routines d'optimisation et de contenu

1. Lire la page ; `pilotage.py etat --statut validee` pour ce projet et ce type
   (`optimisation` ou `contenu` ; les `decision` attendent l'humain).
2. Avant de commencer : `marquer --statut en-cours`, publier.
3. Exécuter selon les skills habituels ; la note du client sur l'action fait foi.
4. Fini : `marquer --statut faite --lien <PR ou URL>`, publier. Bloqué par
   quelqu'un ou quelque chose : `marquer --statut bloquee --attend "<qui ou quoi>"`.
5. Sans action validée, la routine fait son travail ordinaire dans les limites
   de `decupler-seo.config.yml` (optimisations à faible risque seulement).

## Une routine ne reste jamais bloquée

Personne ne répond pendant une routine. **Une routine ne fusionne jamais sa
propre PR** : la politique de sécurité des sessions refuse une fusion sans
relecture, et une routine qui pose la question « fusionner ? » reste bloquée
jusqu'à la réponse (constaté le 02/10/2026 : un vendredi entier perdu). Elle
laisse la PR ouverte, l'écrit dans le journal de run, ajoute sur la page de suivi
`pilotage.py ajouter --titre "Fusionner la PR <n°>" --type decision --chantier pilotage --statut bloquee --attend "relire et fusionner" --lien <PR>`,
publie, et termine. Même conduite pour toute étape refusée (suppression,
push sur main…) : ne pas insister, ne pas attendre de réponse. Le tableau de bord est mis à jour **avant** la livraison
git : un refus de fusion ne doit jamais coûter la roadmap du mois.
