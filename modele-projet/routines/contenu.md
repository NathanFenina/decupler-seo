# Contenu — chaque semaine

Lis `routines/_commun.md`, puis :

## Roadmap d'abord
1. Lis la page de suivi ; `pilotage.py etat --statut validee` pour ce projet.
2. Exécute d'abord les actions validées de type « contenu » (même marquage que l'optimisation).

## Puis les pages de la semaine
1. Sujet : action validée, sinon le calendrier (`rapports/calendrier-*.md`) ; jamais un
   mot-clé déjà porté par une autre page de la même langue (`memoire/cartographie.csv`).
2. `serp_concurrents.py`, brief avec triplets (`seo-entites-triplets`), rédaction dans le
   style de `memoire/style.md`, design (`seo-design-pages`), images, contrôles bloquants.
3. Publication selon `publication.mode` : `cms` → brouillon ; `depot` → PR.
   Ajoute chaque page à `rapports/a-valider.md`, au journal (page-neuve) et à la cartographie.
4. Plafond : `pages_max` de la config. Qualité avant volume.
