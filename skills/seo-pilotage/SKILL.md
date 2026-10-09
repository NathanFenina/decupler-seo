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

## Un programme sur plusieurs mois

La page est organisée en six vues :

- **Synthèse** : clics et impressions du dernier bilan, actions à valider,
  bloquées, en cours et faites ce mois, les 5 décisions les plus urgentes
  (boutons compris), avancement par chantier, courbe des clics.
- **À décider** : d'abord ce qui est bloqué, regroupé par personne attendue
  (`attend`), puis ce qui est à valider, par chantier, avec Valider / Refuser
  et une remarque pour Claude. Les décisions programmées plus tard sont
  repliées à part.
- **Roadmap** : matrice chantier × mois, du premier mois des actions à six
  mois après le mois en cours ; chaque case compte les actions par statut, un
  clic ouvre le mois en couloirs par chantier.
- **Plan d'actions** : toutes les actions, recherche et filtres (chantier,
  statut, mois, qui), avec un compteur.
- **Backlinks** : le plan de netlinking **mois par mois** (`projet.backlinks`) :
  synthèse, brief et documents, indicateurs, frise des mois, puis pour le mois
  choisi l'objectif, le budget, « qui fait quoi » (tâches par personne, reliées
  aux actions par leur id), les cibles du mois, les liens obtenus et les actions
  off-page ; ensuite les pages à pousser, les règles du jeu et tous les liens.
- **Reporting** : un onglet par mois (reporting, fait, à faire, wins,
  contenus, liens du mois, semaine par semaine, cartographie). Le contenu
  hôte d'une page intégrée reste dans l'onglet de son mois.

L'en-tête est celui d'un programme : surtitre, titre, introduction et ardoise
(période, actions, décisions, mise à jour) ; la roadmap porte une frise des
phases alignée sur les mois. Les deux s'écrivent avec
`pilotage.py programme --fichier programme.json`
(`{surtitre, intro, debut, fin, phases: [{titre, debut, fin, texte}]}`).

Le plan de netlinking s'écrit avec `pilotage.py backlinks --fichier plan.json` :
`{synthese, responsable, brief: {titre, url}, documents, indicateurs: [{nom, depart,
cible_3m, cible_6m, mesure}], pages: [{page, requete, depart, liens, note}],
regles: [{titre, texte}], mois: {"AAAA-MM": {titre, objectif, cible, budget, temps,
taches: [{qui, texte, statut | action}], cibles: [{nom, priorite, type, etat, cout,
lien, url}]}}}`. Une tâche qui porte `action` (id d'une action) affiche le statut
de cette action ; sinon `statut` : `a-faire`, `en-cours`, `fait`, `bloque`.
Relancé, il met à jour sans rien doubler (tâche repérée par son texte, cible
par son nom). Jamais d'identifiant, de mot de passe ni de détail de sécurité
dans ce plan : la page se partage et sa copie part dans git.

Le mois d'une action est son `mois_cible` s'il existe, sinon son `mois`. Une
action faite se range dans le mois de sa date (`maj`) ; une action ouverte d'un
mois passé glisse dans le mois en cours. Pour reprendre un historique :
`ajouter --date AAAA-MM-JJ`.

Programmer une action dans un mois à venir :
`pilotage.py mois-cible --id <id> --mois AAAA-MM` (`--retirer` pour la rendre à
son mois), ou `ajouter … --mois-cible AAAA-MM`. **Une action validée programmée
plus tard n'est pas lancée avant son mois** : `etat --statut validee` ne la liste
pas (`--toutes` pour la voir).

Consigner un lien obtenu (reporting mensuel du consultant ou de la routine) :
`pilotage.py lien --url <page qui fait le lien> --cible /page/ --ancre "…" --prix 180
--attribut dofollow --statut en-ligne --date AAAA-MM-JJ` (`--domaine` est déduit
de l'URL). Une URL déjà consignée est mise à jour, jamais dupliquée.

Qui porte une action : `qui` s'il est renseigné (`ajouter --qui`), sinon la
personne nommée avant « : » dans `attend`, sinon le décideur (`decideur` du
projet, Nathan par défaut) pour ce qui est à valider ou bloqué, et Claude pour
le reste.

Le bilan d'une semaine ou d'un mois s'écrit avec `pilotage.py mois --fichier
<json>` (format dans `routines/hebdo.md`) : relancé, il ne double rien. Le
lien de la base Notion des contenus va dans le projet (`notion`), celui de
chaque contenu dans sa ligne.

## Aux couleurs du projet

Chaque projet garde sa charte : `pilotage.py injecter --theme theme.json`, avec
les jetons du design system du client (`mode` sombre ou clair, `fond`, `carte`,
`encre`, `doux`, `trait`, `accent`, `accent_doux`, `cta`, `cta_texte`, `lien`,
`titre`, `texte`, `polices` = URL Google Fonts). En mode sombre, la page suit
la marque quel que soit le thème du lecteur. Pour suivre le thème du lecteur
(clair ou sombre), ajouter `clair` (et au besoin `sombre`) : des jetons qui
remplacent ceux du thème dans ce mode, par exemple
`{"mode": "auto", "fond": "#07080f", …, "clair": {"fond": "#f6f5fb", "encre": "#12131f", …}}`.
Jetons possibles en plus : `creux` (fonds de tableaux et frise), `encre2` (texte
secondaire), `attente`, `ok`, `non`, `info` et leurs `_doux`, `chiffre`. Vérifier les contrastes (texte
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
2. `scripts/pilotage.py` travaille sur ce fichier (`etat`, `injecter`, `marquer`,
   `ajouter`, `mois-cible`, `lien`, `mois`).
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
