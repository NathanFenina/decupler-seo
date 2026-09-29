# GSC — Chute trafic

**Groupe :** Diagnostiquer · **Source :** Google Search Console

## La question à laquelle ce skill répond

J'ai perdu du trafic : est-ce le classement, le CTR, ou la demande qui a baissé ?

## Données à récupérer

Deux périodes comparables (même longueur, mêmes jours de semaine) : clics, impressions, CTR, position.

Accès aux données : voir « Récupérer les données » dans `../SKILL.md`.

## Méthode

1. Décomposer la variation de clics en trois causes : **position** (position moyenne dégradée), **CTR** (position stable mais moins de clics), **demande** (impressions en baisse à position constante).
2. Chiffrer la part de chaque cause dans la perte totale — c'est le cœur du diagnostic.
3. Descendre au niveau URL pour les 10 plus grosses pertes.
4. Vérifier `gsc-saisonnalite` avant de conclure à un problème.

## Sortie attendue

Un verdict en une phrase (« 70 % de la perte vient du CTR, pas du classement ») + le détail par cause et par URL.

## Le prompt

```
Contexte : site {domaine}. J'ai perdu du trafic organique.
Objectif : savoir de quoi vient la perte avant de corriger quoi que ce soit.

1. Prends les 28 derniers jours et les 28 précédents. Vérifie que les
   deux périodes contiennent le même nombre de chaque jour de semaine.
2. Décompose la variation de clics en trois causes :
   - POSITION : je suis moins bien classé qu'avant
   - CTR : je suis classé pareil mais on me clique moins
   - DEMANDE : mes impressions baissent à position constante
3. Chiffre la part de chaque cause dans la perte totale, en clics et en
   pourcentage. C'est le cœur de la réponse — commence par ça.
4. Descends au niveau URL pour les 10 plus grosses pertes et refais la
   même décomposition sur chacune.
5. Avant de conclure à un problème, vérifie la saisonnalité : compare
   au même mois de l'année précédente.

Rends d'abord un verdict en une phrase du type « 70 % de la perte vient
du CTR, pas du classement », puis le détail par cause et par URL.
Termine par ce que je dois corriger en premier.

Ne jamais inventer un chiffre : si la donnée manque ou si le volume
est trop faible pour conclure, dis-le explicitement.
Indique toujours la période et le volume qui portent tes conclusions.
```

Règles communes : voir `../SKILL.md`.
