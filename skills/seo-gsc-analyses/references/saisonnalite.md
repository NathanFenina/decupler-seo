# GSC — Saisonnalite

**Groupe :** Diagnostiquer · **Source :** Google Search Console

## La question à laquelle ce skill répond

Cette baisse est-elle un problème, ou mon creux annuel habituel ?

## Données à récupérer

16 mois d'historique minimum, par mois.

Accès aux données : voir « Récupérer les données » dans `../SKILL.md`.

## Méthode

1. Comparer le mois courant au **même mois de l'année précédente**, pas au mois précédent.
2. Calculer l'indice saisonnier de chaque mois sur l'historique disponible.
3. Décider si l'écart observé sort de la fourchette saisonnière normale.
4. Le dire franchement quand il n'y a pas assez d'historique pour conclure.

## Sortie attendue

Un verdict : saisonnier attendu / anomalie réelle / historique insuffisant, avec le graphique année sur année.

## Le prompt

```
Contexte : site {domaine}. Mon trafic baisse et je ne sais pas
si je dois m'inquiéter.
Objectif : séparer le cycle normal de l'anomalie réelle.

1. Récupère au moins 16 mois d'historique mensuel : clics, impressions.
2. Compare le mois courant au MÊME MOIS de l'année précédente, pas au
   mois précédent. C'est toute la différence.
3. Calcule l'indice saisonnier de chaque mois sur l'historique
   disponible, et la fourchette normale de variation.
4. Situe l'écart observé : est-il dans la fourchette saisonnière, ou
   en sort-il ?
5. Si l'historique est trop court pour établir un cycle (moins de deux
   passages sur le même mois), dis-le franchement au lieu de conclure.

Rends un verdict clair en trois options : saisonnier attendu, anomalie
réelle, ou historique insuffisant. Appuie-le sur le tableau année contre
année, mois par mois. Si c'est une anomalie, enchaîne sur une
décomposition position / CTR / demande.

Ne jamais inventer un chiffre : si la donnée manque ou si le volume
est trop faible pour conclure, dis-le explicitement.
Indique toujours la période et le volume qui portent tes conclusions.
```

Règles communes : voir `../SKILL.md`.
