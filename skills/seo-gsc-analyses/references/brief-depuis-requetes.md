# GSC — Brief depuis requetes

**Groupe :** Produire · **Source :** Google Search Console

## La question à laquelle ce skill répond

Comment écrire un brief à partir de ce que les gens tapent vraiment, pas de ce qu'un outil suggère ?

## Données à récupérer

Requêtes d'une page ou d'un cluster, 6 mois.

Accès aux données : voir « Récupérer les données » dans `../SKILL.md`.

## Méthode

1. Partir des requêtes réelles : elles portent le vocabulaire exact des acheteurs.
2. Grouper par intention, puis ordonner les groupes par volume d'impressions — cet ordre devient le plan Hn.
3. Extraire les formulations interrogatives : elles deviennent des H3 ou des entrées de FAQ.
4. Compléter avec la SERP (via DataForSEO ou Firecrawl) uniquement pour ce que GSC ne peut pas dire : ce que couvrent les concurrents.

## Sortie attendue

Un brief : angle, plan Hn ordonné, vocabulaire imposé, questions à traiter, et le volume d'impressions qui justifie chaque section.

## Le prompt

```
Contexte : site {domaine}, cluster ou page {page}.
Objectif : un brief bâti sur ce que les gens tapent vraiment, pas sur ce
qu'un outil de volume suggère.

1. Récupère les requêtes du cluster sur 6 mois : impressions, clics,
   position, page servie.
2. Groupe par intention, puis ordonne les groupes par impressions.
   Cet ordre devient le plan Hn — le sujet le plus cherché passe en
   premier, pas celui qui t'arrange.
3. Extrais les formulations interrogatives : elles deviennent des H3 ou
   des entrées de FAQ.
4. Relève le VOCABULAIRE EXACT des requêtes. C'est le langage de mes
   acheteurs : impose-le dans le brief, ne le reformule pas en jargon.
5. Complète avec la SERP (DataForSEO ou Firecrawl) UNIQUEMENT pour ce
   que Search Console ne peut pas dire : ce que couvrent les
   concurrents et que je ne couvre pas.

Rends un brief : angle éditorial, plan Hn ordonné avec le volume qui
justifie chaque section, vocabulaire imposé, questions à traiter, et
longueur cible. Précise pour chaque section si elle vient de mes
données ou de l'analyse SERP.

Ne jamais inventer un chiffre : si la donnée manque ou si le volume
est trop faible pour conclure, dis-le explicitement.
Indique toujours la période et le volume qui portent tes conclusions.
```

Règles communes : voir `../SKILL.md`.
