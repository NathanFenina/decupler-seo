# GSC — Requetes neuves

**Groupe :** Diagnostiquer · **Source :** Google Search Console

## La question à laquelle ce skill répond

Sur quelles requêtes Google a-t-il commencé à me montrer, sans que j'aie de page dédiée ?

## Données à récupérer

Deux périodes de 28 jours consécutives, dimension `query`.

Accès aux données : voir « Récupérer les données » dans `../SKILL.md`.

## Méthode

1. Isoler les requêtes présentes sur la période récente et **absentes** de la précédente.
2. Écarter le bruit : exiger un seuil d'impressions.
3. Pour chaque requête neuve, identifier la page qui la reçoit et juger si elle est la bonne.
4. Regrouper les requêtes neuves par thème : un cluster émergent vaut une page, pas une ligne.

## Sortie attendue

Les requêtes émergentes groupées par thème, avec la page actuellement servie et un verdict : page adaptée / à enrichir / à créer.

## Le prompt

```
Contexte : site {domaine}.
Objectif : attraper les sujets sur lesquels Google commence à me tester.

1. Compare les 28 derniers jours aux 28 précédents, dimension requête.
2. Isole les requêtes présentes sur la période récente et TOTALEMENT
   absentes de la précédente.
3. Écarte le bruit : exige au moins 20 impressions sur la période
   récente. Écarte aussi les requêtes de marque.
4. Pour chaque requête neuve, identifie la page qui la reçoit
   aujourd'hui et juge si c'est la bonne : Google me sert-il une page
   pertinente, ou une page par défaut faute de mieux ?
5. Regroupe les requêtes neuves par thème. Un cluster émergent mérite
   une page dédiée, une requête isolée ne mérite qu'une section.

Rends les clusters émergents triés par impressions cumulées, avec pour
chacun : les requêtes qui le composent, la page actuellement servie, sa
position, et un verdict en trois options — page adaptée, page à
enrichir, page à créer.

Ne jamais inventer un chiffre : si la donnée manque ou si le volume
est trop faible pour conclure, dis-le explicitement.
Indique toujours la période et le volume qui portent tes conclusions.
```

Règles communes : voir `../SKILL.md`.
