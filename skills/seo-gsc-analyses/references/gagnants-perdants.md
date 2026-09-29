# GSC — Gagnants perdants

**Groupe :** Diagnostiquer · **Source :** Google Search Console

## La question à laquelle ce skill répond

Qu'est-ce qui monte et qu'est-ce qui tombe depuis le mois dernier ?

## Données à récupérer

Deux périodes comparables, par `page` et par `query`.

Accès aux données : voir « Récupérer les données » dans `../SKILL.md`.

## Méthode

1. Comparer clics, impressions et position sur des périodes de longueur identique.
2. Classer séparément les gains et les pertes, en valeur absolue.
3. Pour chaque mouvement important, donner la cause probable (renvoyer vers `gsc-chute-trafic`).
4. Ne jamais présenter un pourcentage sans le volume associé.

## Sortie attendue

Deux tableaux (top gains / top pertes) avec volume, variation, et cause probable.

## Le prompt

```
Contexte : site {domaine}.
Objectif : voir ce qui a bougé ce mois-ci, et de combien.

1. Compare le mois écoulé au précédent, sur des périodes de longueur
   strictement identique. Fais-le par page ET par requête.
2. Classe séparément les gains et les pertes, en VALEUR ABSOLUE de
   clics. Un +300 % sur 4 clics n'intéresse personne.
3. Pour chacun des 10 plus gros mouvements dans chaque sens, donne la
   cause probable : position, CTR, ou demande.
4. Ne présente jamais un pourcentage sans le volume à côté.
5. Signale à part les pages qui apparaissent ou disparaissent
   complètement — ce sont souvent des problèmes techniques, pas
   éditoriaux.

Rends deux tableaux (top 10 gains, top 10 pertes) : URL ou requête |
clics avant | clics après | variation absolue | variation % | cause
probable. Termine par les 3 mouvements qui expliquent l'essentiel de la
variation globale.

Ne jamais inventer un chiffre : si la donnée manque ou si le volume
est trop faible pour conclure, dis-le explicitement.
Indique toujours la période et le volume qui portent tes conclusions.
```

Règles communes : voir `../SKILL.md`.
