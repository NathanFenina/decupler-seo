# GSC — Ctr anormal

**Groupe :** Diagnostiquer · **Source :** Google Search Console

## La question à laquelle ce skill répond

Quelles pages sous-performent en clics compte tenu de la position qu'elles occupent déjà ?

## Données à récupérer

`query` + `page`, 28 jours : impressions, clics, CTR, position.

Accès aux données : voir « Récupérer les données » dans `../SKILL.md`.

## Méthode

1. Établir la **courbe CTR/position du site** (CTR médian observé pour chaque position) — c'est la référence, pas un standard générique.
2. Repérer les pages dont le CTR est nettement sous la médiane de leur propre position.
3. Filtrer sur un minimum d'impressions pour éviter les faux positifs statistiques.
4. Vérifier la SERP : un AI Overview ou un featured snippet concurrent explique parfois tout le déficit.

## Sortie attendue

Les pages à fort potentiel de CTR, avec l'écart chiffré à la courbe. Passer la main à `gsc-reecriture-title`.

## Le prompt

```
Contexte : site {domaine}.
Objectif : récupérer les clics que je laisse sur la table à position égale.

1. Récupère les couples (requête, page) sur 28 jours : impressions,
   clics, CTR, position.
2. Construis d'abord la courbe CTR/position de MON site : pour chaque
   position entière, le CTR médian que j'observe réellement. C'est la
   référence — un standard générique du marché ne vaut rien ici.
3. Repère les pages dont le CTR est nettement sous la médiane de leur
   PROPRE position. Exige au moins 200 impressions pour éviter les faux
   positifs statistiques.
4. Pour les 10 pires écarts, vérifie la SERP : un AI Overview, un
   featured snippet concurrent ou un bloc shopping expliquent parfois
   tout le déficit. Dans ce cas, dis-le — ce n'est pas un problème de
   title.
5. Chiffre le manque à gagner : impressions × (CTR médian − CTR actuel).

Rends un tableau : URL | requête | position | CTR actuel | CTR médian à
cette position | écart | clics perdus/mois. Sépare clairement les cas
« title à réécrire » des cas « la SERP me vole le clic ».

Ne jamais inventer un chiffre : si la donnée manque ou si le volume
est trop faible pour conclure, dis-le explicitement.
Indique toujours la période et le volume qui portent tes conclusions.
```

Règles communes : voir `../SKILL.md`.
