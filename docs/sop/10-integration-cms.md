<!-- SOP decupler-seo · source unique : docs/sop/ · le playbook public https://decupler.com/claude-code-seo-os/ en reprend le contenu -->

# SOP 10 · Intégration CMS

**Skills** : `seo-publication-cms` · **Commande** : `/seo publish`

**Objectif** : Publier sans copier-coller, sans jamais casser la page en ligne.

**Quand** : Chaque fois qu'un contenu est prêt.

**Dis à Claude** : « Publie cette page en brouillon sur WordPress, avec son title, sa meta et son image, et donne-moi le lien d'aperçu. »

## Étapes

1. Crée un mot de passe d'application WordPress (Utilisateurs → Profil). Jamais ton mot de passe de connexion.
2. `wp.py verifier` contrôle les droits, l'extension SEO et les champs ouverts à l'API.
3. Le garde-fou (`guard.py`) répond : autorisé, à valider, ou bloqué.
4. `wp.py publier` : brouillon par défaut, sauvegarde avant écriture, contrôle du contenu, puis lien d'aperçu. Une page déjà en ligne est modifiée en révision : la version publique ne bouge pas.
5. Vérification sur la page réelle après publication, puis la modification entre au journal, pour être mesurée à J+28.

**MCP nécessaires** : WordPress ou Webflow, ou directement l'API REST par `wp.py`.

**Livrable** : Le brouillon, son lien d'aperçu, la sauvegarde et la ligne du journal.

## Pièges

- Yoast n'ouvre pas title et meta à l'API par défaut : sans un petit plugin qui les expose, WordPress répond 200 et jette les valeurs.
- WordPress transforme les lignes vides en paragraphes, y compris dans un `<style>` : la page casse en ligne alors qu'elle était parfaite en local.
- Mettre un `<h1>` dans le contenu quand le thème affiche déjà le titre.
