# GSC — Maillage

**Groupe :** Produire · **Source :** Google Search Console

## La question à laquelle ce skill répond

Quels liens internes ajouter, et depuis quelles pages exactement ?

## Données à récupérer

Requêtes par page sur tout le site.

Accès aux données : voir « Récupérer les données » dans `../SKILL.md`.

## Méthode

1. Calculer la proximité sémantique entre pages à partir du recouvrement de leurs requêtes.
2. Proposer un lien quand une page A reçoit des requêtes proches du sujet d'une page B mieux positionnée.
3. Proposer l'ancre à partir de la requête réelle partagée, jamais une ancre générique.
4. Prioriser les liens venant des pages qui reçoivent déjà du trafic — un lien depuis une page morte ne vaut rien.

## Sortie attendue

Un tableau : page source, page cible, ancre proposée, requête qui la justifie, trafic de la page source.

## Le prompt

```
Contexte : site {domaine}.
Objectif : ajouter les liens internes qui manquent, avec les bonnes ancres.

1. Récupère les requêtes par page sur l'ensemble du site, 6 mois.
2. Calcule la proximité entre pages à partir du RECOUVREMENT de leurs
   requêtes — pas d'une similarité de titre.
3. Propose un lien quand une page A reçoit des requêtes proches du sujet
   d'une page B mieux positionnée sur ces requêtes.
4. Déduis l'ancre de la requête réelle partagée. Jamais « cliquez ici »,
   jamais une ancre générique, jamais l'URL nue.
5. Ne pars QUE de pages qui reçoivent déjà du trafic : un lien depuis
   une page que personne ne visite ne transmet rien.
6. Vérifie que le lien n'existe pas déjà avant de le proposer.

Rends un tableau : page source | trafic de la source | page cible |
ancre proposée | requête qui justifie le lien | où l'insérer dans la
page source. Trie par impact attendu, et limite-toi à 20 liens pour
rester actionnable.

Ne jamais inventer un chiffre : si la donnée manque ou si le volume
est trop faible pour conclure, dis-le explicitement.
Indique toujours la période et le volume qui portent tes conclusions.
```

Règles communes : voir `../SKILL.md`.
