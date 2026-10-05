<!-- SOP decupler-seo · source unique : docs/sop/ · le playbook public https://decupler.com/claude-code-seo-os/ en reprend le contenu -->

# SOP 5 · Optimisation on-page

**Skills** : `seo-optimisation-onpage`, `seo-meta-serp`, `seo-quick-wins` · **Commande** : `/seo onpage <url> <mot-clé>`

**Objectif** : Noter une page existante sur 100 face à son mot-clé, puis la réécrire.

**Quand** : Pour toute page en position 4 à 20 : c'est là que l'effort rapporte le plus vite.

**Dis à Claude** : « Note cette page sur 100 pour « claude code seo », critère par critère, puis réécris-la. »

## Étapes

1. Donne le mot-clé cible. Sans cible, il n'y a pas d'optimisation possible.
2. `onpage_score.py` mesure les balises, la structure, le contenu, la sémantique et la lisibilité : un feu vert, jaune ou rouge par critère, et un malus de sur-optimisation.
3. Claude compare au top 3 : entités, sous-sujets et questions qui manquent.
4. Il réécrit la version complète, prête à coller, et propose 3 titles et 2 metas avec l'aperçu dans Google.
5. Les requêtes Search Console de la page qui ont des impressions sans clic deviennent des sections ou des questions de FAQ.

**MCP nécessaires** : Search Console. DataForSEO ou Firecrawl pour le top 3.

**Livrable** : Le rapport noté sur 100 et la version réécrite, avec title et meta.

## Pièges

- Une meta hors de 120 à 156 caractères.
- Répéter le mot-clé partout : la note baisse, et la page aussi.
- Juger un changement au lendemain. On mesure à J+28, contre les pages qui n'ont pas bougé.
