<!-- SOP decupler-seo · source unique : docs/sop/ · le playbook public https://decupler.com/claude-code-seo-os/ en reprend le contenu -->

# SOP 4 · Rédaction

**Skills** : `seo-redaction`, `seo-eeat` · **Commande** : `/seo article`

**Objectif** : Un texte qui se lit comme le tien, sourcé, sans remplissage, prêt à être cité.

**Quand** : Après un brief validé.

**Dis à Claude** : « Rédige la page à partir de ce brief, dans mon style, puis note-la en E-E-A-T avant de me la rendre. »

## Étapes

1. Vérifier qu'il faut écrire : aucune page du site ne vise déjà la même intention.
2. Recherche obligatoire : lecture réelle du top 3, et chaque chiffre vérifié à sa source.
3. Une thèse avant un plan : ce que ta page affirme et que les autres ne disent pas.
4. Rédaction par l'agent `seo-redacteur`, dans ton style mesuré (`memoire/style.md`), une donnée par paragraphe.
5. Test anti-remplissage sur chaque paragraphe, puis note E-E-A-T sur 40 et correctifs localisés.
6. `controle_contenu.py` bloque toute promesse ou tout chiffre sans source avant publication.

**MCP nécessaires** : DataForSEO ou Firecrawl pour la recherche. WordPress pour le brouillon.

**Livrable** : La page en HTML ou en Markdown, ses sources, son schema, et le verdict E-E-A-T (publier, réviser ou réécrire).

## Pièges

- Un chiffre sans source : le contrôle bloque, et c'est voulu.
- Deux pages d'un même gabarit qui se lisent pareil.
- Un avis, une note, une anecdote ou une référence client inventés. Jamais.
