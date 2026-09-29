# GSC — Sections manquantes

**Groupe :** Produire · **Source :** Google Search Console

## La question à laquelle ce skill répond

Quelles questions cette page reçoit-elle sans y répondre ?

## Données à récupérer

Toutes les requêtes servies par UNE URL, 3 mois.

Accès aux données : voir « Récupérer les données » dans `../SKILL.md`.

## Méthode

1. Récupérer l'intégralité des requêtes que la page reçoit, y compris celles à faibles impressions.
2. Les regrouper en intentions distinctes.
3. Confronter chaque intention au contenu réel de la page : la traite-t-elle explicitement, ou Google l'a-t-il servie par défaut ?
4. Ne proposer que les sections **absentes** — ne jamais réécrire ce qui existe déjà.

## Sortie attendue

La liste des sections à ajouter, avec pour chacune les requêtes qui la justifient et le volume d'impressions en jeu.

## Le prompt

```
Contexte : page {page} du site {domaine}.
Objectif : trouver ce que cette page reçoit comme questions sans y répondre.

1. Récupère TOUTES les requêtes servies par cette URL sur 3 mois, y
   compris celles à faibles impressions — c'est souvent là que se
   cachent les trous.
2. Regroupe-les en intentions distinctes (pas en mots-clés : en
   intentions).
3. Lis le contenu réel de la page. Pour chaque intention, tranche :
   la page la traite-t-elle EXPLICITEMENT, ou Google l'a-t-il servie
   par défaut faute de meilleure candidate ?
4. Ne propose que les sections ABSENTES. Ne réécris jamais ce qui
   existe déjà — ce n'est pas la mission.
5. Pour chaque section proposée, cite les requêtes qui la justifient et
   le total d'impressions en jeu.

Rends la liste des sections à ajouter, ordonnée par impressions
couvertes, avec pour chacune : le titre Hn proposé, les requêtes
justificatives, le volume, et deux lignes sur ce que la section doit
dire. Termine par le total d'impressions actuellement mal servies.

Ne jamais inventer un chiffre : si la donnée manque ou si le volume
est trop faible pour conclure, dis-le explicitement.
Indique toujours la période et le volume qui portent tes conclusions.
```

Règles communes : voir `../SKILL.md`.
