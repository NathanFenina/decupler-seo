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

Statuts d'une action : `proposee` → `validee` (ou `refusee`) → `en-cours` → `faite`.

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

## Routine de rapport — le 1er du mois

Après `cartographie.py mensuel` et `rapport.py` :
```bash
python3 <scripts>/pilotage.py donnees --sortie donnees/pilotage.json
python3 <scripts>/pilotage.py proposer --mois <AAAA-MM> --projet-id <id> --sortie donnees/actions-<AAAA-MM>.json
python3 <scripts>/pilotage.py injecter --html donnees/tableau-de-bord.html --projet-id <id> \
  --donnees donnees/pilotage.json --actions donnees/actions-<AAAA-MM>.json
```
puis publier. Au plus 8 actions par mois, dont au plus 3 décisions. Une action
refusée ne revient pas ; une décision prise n'est jamais écrasée.

## Routines d'optimisation et de contenu

1. Lire la page ; `pilotage.py etat --statut validee` pour ce projet et ce type
   (`optimisation` ou `contenu` ; les `decision` attendent l'humain).
2. Avant de commencer : `marquer --statut en-cours`, publier.
3. Exécuter selon les skills habituels ; la note du client sur l'action fait foi.
4. Fini : `marquer --statut faite --lien <PR ou URL>`, publier. Bloqué :
   remettre `validee` avec `--note` qui dit pourquoi.
5. Sans action validée, la routine fait son travail ordinaire dans les limites
   de `decupler-seo.config.yml` (optimisations à faible risque seulement).
