<!-- SOP decupler-seo · source unique : docs/sop/ · le playbook public https://decupler.com/claude-code-seo-os/ en reprend le contenu -->

# SOP 17 · Travailler avec un prestataire

**Skills** : tous, selon la tâche · **Commande** : `/seo doctor`, puis la SOP de la tâche

**Objectif** : Qu'un rédacteur, un intégrateur ou un consultant produise au même niveau que vous, sur le même projet, sans rien casser et sans tout réexpliquer.

**Quand** : À l'arrivée d'un prestataire sur un projet, puis à chaque tâche confiée.

**Dis à Claude** : « Je suis prestataire sur ce projet : lis la mémoire, dis-moi les règles, puis prépare la tâche "<tâche>" en suivant sa SOP. »

## Étapes

1. **Accès, le minimum** : le dépôt du projet (droit d'écriture, jamais sur la branche principale), le CMS avec un rôle d'éditeur, Search Console en lecture. Les clés lui sont données hors du dépôt ; il les met dans son propre `.env`.
2. **Installation** : Claude Code, puis `git clone` du dépôt ; la méthode est déjà dedans (`.claude/`). `/seo doctor` dit ce qui manque sur son poste.
3. **Lecture obligatoire avant la première tâche** : `Accueil.md`, `CLAUDE.md`, `memoire/marque.md`, `memoire/style.md`, `memoire/decisions.md`, et la SOP de sa tâche.
4. **Une tâche = une action validée de la page de suivi = une branche = une PR.** Le prestataire travaille sur `presta/<prénom>-<tâche>`, suit la SOP, passe les contrôles (`controle_contenu.py`, `humanisation.py`), ouvre la PR. Vous relisez et fusionnez.
5. **Une amélioration de méthode ?** Elle ne se fait pas en douce dans `.claude/` : il la propose dans la PR, et vous la remontez dans decupler-seo (`projet.py remonter`) si elle vaut pour tous.

**MCP nécessaires** : ceux de la tâche ; aucun accès en écriture à la production sans validation.

**Livrable** : Des PR qui suivent les SOP, journalisées, relues.

## Pièges

- Donner un compte administrateur WordPress ou la clé Search Console en écriture : personne n'en a besoin pour rédiger ou optimiser.
- Laisser un prestataire publier sans PR : la modification ne sera ni journalisée ni mesurée.
- Lui laisser inventer un chiffre « pour illustrer » : la règle `memoire/faits.md` vaut pour tout le monde.
- Lui demander d'écrire sans `memoire/style.md` : le texte sonnera juste, mais pas comme le client.
