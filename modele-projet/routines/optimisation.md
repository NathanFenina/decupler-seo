# Optimisation — chaque semaine

Lis `routines/_commun.md`, puis :

## Roadmap d'abord
1. Lis la page de suivi ; `python3 .claude/decupler-seo/scripts/pilotage.py etat --html donnees/tableau-de-bord.html --projet-id <pilotage.projet_id> --statut validee`.
2. Exécute d'abord les actions validées de type « optimisation », en respectant leur note :
   `pilotage.py marquer --id <id> --statut en-cours` et republie ; livrée : `--statut faite --lien <PR ou URL>` et republie ;
   bloquée : `--statut validee --note "<pourquoi>"`.

## Puis le travail de la semaine
1. Skill `seo-cycle` en mode optimisation, pages choisies par `seo-opportunites`,
   plafonds de `decupler-seo.config.yml`. Aucune page neuve ici.
2. Journalise chaque modification (`journal.py ajouter --auto`) avant de passer à la suivante.
3. Publication selon `publication.mode` : `cms` → par `wp.py` (ou le CMS), en révision ou brouillon ;
   `depot` → contrôles bloquants (`controle.commandes`), puis PR qui liste page, requête visée, gain attendu.
4. Fusion de la PR seulement si la config et `memoire/decisions.md` l'autorisent ; sinon PR ouverte.
