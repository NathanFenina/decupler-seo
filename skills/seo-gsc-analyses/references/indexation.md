# GSC — Indexation

**Groupe :** Piloter · **Source :** Google Search Console

## La question à laquelle ce skill répond

Qu'est-ce qui n'est pas indexé, et pourquoi ?

## Données à récupérer

Rapport de couverture + inspection d'URL + sitemap.

Accès aux données : voir « Récupérer les données » dans `../SKILL.md`.

## Méthode

1. Confronter les URLs du sitemap aux URLs réellement indexées.
2. Classer les exclusions par motif : découverte sans indexation, explorée non indexée, canonique différente, 404, redirection.
3. Traiter en priorité les pages qui comptent — une page de pagination non indexée n'est pas un problème.
4. Pour chaque motif, donner la correction concrète, pas juste le constat.

## Sortie attendue

Les pages non indexées qui comptent, groupées par motif, avec l'action de correction.

## Le prompt

```
Contexte : site {domaine}.
Objectif : savoir ce qui n'est pas indexé, et surtout si c'est grave.

1. Confronte les URLs du sitemap aux URLs réellement indexées.
2. Classe les exclusions par MOTIF : découverte sans indexation,
   explorée non indexée, canonique différente, 404, redirection,
   bloquée par robots.txt, balise noindex.
3. Trie par importance business, pas par volume. Une page de
   pagination non indexée n'est pas un problème ; ta page service
   principale non indexée en est un.
4. Pour chaque motif, donne la correction CONCRÈTE, pas le constat.
   « Explorée non indexée » veut souvent dire contenu trop faible ou
   trop proche d'une autre page : dis laquelle.
5. Signale les pages indexées qui NE sont PAS dans le sitemap —
   c'est l'angle mort habituel.

Rends : le compte par motif, puis les pages qui comptent vraiment,
groupées par motif, avec l'action de correction et sa priorité.
Distingue ce qui est normal de ce qui est cassé.

Ne jamais inventer un chiffre : si la donnée manque ou si le volume
est trop faible pour conclure, dis-le explicitement.
Indique toujours la période et le volume qui portent tes conclusions.
```

Règles communes : voir `../SKILL.md`.
