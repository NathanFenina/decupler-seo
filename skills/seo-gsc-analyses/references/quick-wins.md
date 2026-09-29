# GSC — Quick wins

**Groupe :** Diagnostiquer · **Source :** Google Search Console

## La question à laquelle ce skill répond

Quelles pages sont juste sous le seuil de trafic, et lesquelles rapportent le plus vite si on les pousse ?

## Données à récupérer

`query` + `page`, 28 derniers jours : impressions, clics, CTR, position moyenne.

Accès aux données : voir « Récupérer les données » dans `../SKILL.md`.

## Méthode

1. Filtrer les couples (requête, page) en **position 8 à 20** avec au moins 50 impressions sur la période.
2. Estimer le gain : `impressions × (CTR attendu en position 3 − CTR actuel)`. Utiliser une courbe CTR/position de référence, pas une moyenne du site.
3. Agréger par URL et trier par gain estimé décroissant.
4. Écarter les requêtes de marque : elles gonflent le classement sans rien apprendre.

## Sortie attendue

Un tableau URL · requête principale · position · impressions · gain de clics estimé, trié par gain. Top 10 commenté.

## Le prompt

```
Contexte : site {domaine}, marché France.
Objectif : trouver où je gagne le plus de trafic pour le moins d'effort.

1. Récupère les couples (requête, page) sur les 28 derniers jours :
   impressions, clics, CTR, position moyenne.
2. Ne garde que la position 8 à 20, avec au moins 50 impressions.
3. Écarte les requêtes contenant ma marque : elles gonflent le
   classement sans rien m'apprendre.
4. Construis la courbe CTR/position de MON site — le CTR médian que
   j'observe à chaque position. N'utilise pas une courbe standard.
5. Estime le gain par couple :
   impressions × (CTR médian en position 3 − CTR actuel).
6. Agrège par URL, additionne, trie par gain décroissant.

Rends un tableau : URL | requête principale | position | impressions |
gain estimé en clics/mois. Puis commente le top 10 : pour chacune, une
phrase sur ce qui bloque probablement (intention mal servie, page trop
courte, title faible).

Ne jamais inventer un chiffre : si la donnée manque ou si le volume
est trop faible pour conclure, dis-le explicitement.
Indique toujours la période et le volume qui portent tes conclusions.
```

Règles communes : voir `../SKILL.md`.
