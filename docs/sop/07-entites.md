<!-- SOP decupler-seo · source unique : docs/sop/ · le playbook public https://decupler.com/claude-code-seo-os/ en reprend le contenu -->

# SOP 7 · Entités

**Skills** : `seo-entites-triplets`, `geo-llms-txt` · **Commande** : `/seo entités`

**Objectif** : Que Google et les IA comprennent qui tu es et ce que tu fais, et retrouvent les mêmes faits sur toutes tes pages.

**Quand** : Une fois pour le site (l'entité), puis sur chaque page qui énonce des faits : prix, délais, lieux.

**Dis à Claude** : « Vérifie que Google comprend qui est derrière le site, puis liste les faits clés de cette page en triplets. »

## Étapes

1. L'entité : une seule Organisation et une seule Personne, chacune avec un identifiant `@id` unique et ses profils en `sameAs`.
2. Le registre des faits (`memoire/triplets.csv`) : une seule valeur par sujet et par prédicat, par exemple « [ton offre] — coûte — [prix HT] ».
3. Sur chaque page, les 3 à 5 faits clés dans les 200 premiers mots, chacun avec son sujet nommé, jamais un pronom.
4. `triplets.py verifier` signale les faits absents, implicites ou contredits ; `triplets.py coherence` trouve les pages qui disent autre chose.
5. Les entités reliées à Wikidata dans le JSON-LD (`about`, `mentions`), un fichier `llms.txt`, et les robots des IA autorisés dans robots.txt.

**MCP nécessaires** : Aucun obligatoire. Firecrawl ou le navigateur pour lire les pages.

**Livrable** : Le registre des faits, le JSON-LD de l'entité et `llms.txt`.

## Pièges

- « Il coûte… » n'est pas extractible : nomme le sujet dans la phrase.
- Un prix différent sur deux pages, et l'IA ne sait plus lequel citer.
- Baliser une date de création qui contredit ce que dit ton site.

> Chez nous : Sur decupler.com, Nathan Fenina apparaissait sous trois identifiants différents et deux adresses LinkedIn circulaient : tout a été relié à un identifiant par entité, sur 48 pages.
