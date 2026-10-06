<!-- SOP decupler-seo · source unique : docs/sop/ · le playbook public https://decupler.com/claude-code-seo-os/ en reprend le contenu -->

# SOP 16 · Arbitrer : quoi faire ce mois-ci

**Skills** : `seo-opportunites`, `seo-strategiste` (agent), `seo-pilotage` · **Commande** : `/seo opportunites`

**Objectif** : Choisir les 3 à 5 actions du mois par ce qu'elles rapportent, avec les mêmes critères pour le contenu, la technique et le GEO, et dire ce qu'on ne fait pas.

**Quand** : Le premier vendredi du mois, avec le rapport (SOP 14), et chaque fois qu'une idée nouvelle arrive.

**Dis à Claude** : « Propose les actions du mois : contenu, technique et GEO, chiffrées, et dis-moi ce qu'on laisse de côté et pourquoi. »

## Étapes

1. **Une seule échelle** : chaque action candidate reçoit un gain estimé en euros par an (`Trafic = Volume × CTR de la position visée`, puis `× taux de conversion × valeur d'un lead`), un effort (heures) et une probabilité (forte si la page est déjà en position 4 à 20, faible pour une requête neuve très concurrentielle). Ordre = gain × probabilité ÷ effort.
2. **D'abord ce qui bloque** : une erreur technique qui coûte des pages indexées ou des conversions passe avant tout (page clé en 404, noindex accidentel, spam, canonique fausse). Pas de calcul, on corrige.
3. **Ensuite ce qui rank déjà** : les pages en position 4 à 20 (`/seo quickwins`) rapportent plus vite qu'une page neuve. Optimisation on-page, title et meta, enrichissement, maillage.
4. **Puis le contenu neuf, par la ligne éditoriale** (SOP 2) : un mot-clé principal non couvert par une page existante (passe anti-cannibalisation), un service vendu derrière, au plus 3 pages neuves par semaine.
5. **Le GEO en parallèle, pas à la place** : les pages qui portent un prompt principal (cartographie) et que les IA ne citent pas (SOP 13) reçoivent la réponse directe, les entités et les données structurées. On le choisit sur les requêtes où l'AI Overview ou ChatGPT répondent déjà.
6. **Écrire ce qu'on ne fait pas** : chaque action écartée va dans `memoire/decisions.md` avec la raison. Elle ne revient pas le mois suivant sans fait nouveau.
7. Les actions retenues vont sur la page de suivi en « à décider » ; le client ou vous les validez.

**MCP nécessaires** : Search Console ; DataForSEO ou Ubersuggest pour la demande ; GA4 pour la valeur réelle d'une page quand il existe.

**Livrable** : 3 à 5 actions chiffrées sur la page de suivi, et les actions écartées dans `memoire/decisions.md`.

## Pièges

- Classer par volume de recherche : un mot-clé à 200 recherches qui vend peut valoir dix fois un mot-clé à 2 000 qui informe.
- Tout faire en même temps : 3 à 5 actions finies valent mieux que 15 commencées.
- Écrire du contenu pour « faire du GEO » sur des sujets sans demande : on rend citable ce qui a déjà une raison d'exister.
- Ignorer `memoire/decisions.md` : reproposer ce que le client a refusé coûte sa confiance.
