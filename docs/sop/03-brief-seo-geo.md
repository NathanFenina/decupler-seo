<!-- SOP decupler-seo · source unique : docs/sop/ · le playbook public https://decupler.com/claude-code-seo-os/ en reprend le contenu -->

# SOP 3 · Brief SEO/GEO

**Skills** : `seo-brief`, `seo-benchmark`, `seo-serp-analysis` · **Commande** : `/seo brief "<mot-clé>"`

**Objectif** : Un brief adossé à la page de résultats du jour, avec la réponse directe et la FAQ déjà rédigées.

**Quand** : Avant chaque page neuve ou chaque réécriture.

**Dis à Claude** : « Fais le brief SEO/GEO de « audit geo » : la SERP du jour, le top 5 lu, ce que personne ne couvre, la réponse directe et la FAQ. »

## Étapes

1. La SERP en direct : top 10, « Autres questions posées », AI Overview et ses sources (`serp_concurrents.py`, avec DataForSEO). Sans DataForSEO, repli sur Firecrawl, puis sur Ubersuggest.
2. Le top 5 lu page par page : longueur, plan Hn, tableaux, FAQ, schémas, entités citées.
3. La matrice de gap : ce que le top traite, et ce que personne ne traite. C'est là qu'est ton angle.
4. Contrôle de cannibalisation : si une page du site vise déjà cette intention, on l'optimise au lieu d'en créer une autre.
5. Le brief en 18 sections : intention, plan chiffré, H1, réponse directe de 40 à 60 mots, FAQ, prompts IA et fan-out, données structurées, sources E-E-A-T, checklist GEO, liens internes tirés du sitemap.

**MCP nécessaires** : DataForSEO (ou Firecrawl, ou Ubersuggest). Search Console si la page existe déjà.

**Livrable** : Le brief en 18 sections et `recherche/serp-<mot-clé>-<date>.md`, avec l'origine de chaque chiffre.

## Pièges

- Écrire un brief sans avoir regardé la SERP du jour.
- Ce qu'une source ne donne pas s'écrit « non mesuré », jamais « absent ».
- Un volume qu'aucun outil n'a renvoyé s'écrit « n.d. », pas une estimation.

> Chez nous : Brief « audit geo » du 05/10/2026 pour decupler.com : l'AI Overview citait 6 sources, dont aucune des 5 premières pages organiques. Coût des appels : 0,09 $.
