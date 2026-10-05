---
description: Produit un brief rédactionnel complet à partir d'un mot-clé
argument-hint: "<mot-clé> [url de la page cible]"
---
Lancez le skill `seo-brief` sur `$ARGUMENTS`.

Collectez d'abord : SERP live et top 5 lu et mesuré (`serp_concurrents.py`,
avec `--url` si la page existe ; sans DataForSEO, `firecrawl_search` +
`firecrawl_scrape` passés au script par `--serp-firecrawl` et
`--pages-json`), style du client (`memoire/style.md`), questions PAA,
vocabulaire Reddit, volumes (DataForSEO ou Ubersuggest avec le `locId` du
pays), sitemap pour le maillage (`--sitemap`). Ne rédigez jamais un brief
sans avoir regardé la SERP, et n'écrivez aucun chiffre qu'un appel n'a pas
renvoyé (`n.d.` sinon).

Le brief doit inclure la réponse directe (40-60 mots), le H1, l'intro et la
FAQ **déjà rédigés**, les prompts IA et leur fan-out, les données
structurées et la checklist GEO.
