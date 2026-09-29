# GSC — Faq depuis requetes

**Groupe :** Produire · **Source :** Google Search Console

## La question à laquelle ce skill répond

Quelles questions dois-je mettre en FAQ, en me basant sur ce qu'on me demande vraiment ?

## Données à récupérer

Requêtes interrogatives d'une page ou d'un site, 6 mois.

Accès aux données : voir « Récupérer les données » dans `../SKILL.md`.

## Méthode

1. Isoler les requêtes qui commencent par un interrogatif (comment, pourquoi, combien, quel, est-ce que…) ou qui en ont la forme.
2. Dédupliquer les reformulations d'une même question.
3. Trier par impressions et retenir celles qui ne sont pas déjà traitées dans le corps de la page.
4. Rédiger des réponses courtes et autonomes — c'est ce format que les moteurs génératifs citent.

## Sortie attendue

Le bloc FAQ rédigé + le JSON-LD `FAQPage` correspondant, prêt à coller.

## Le prompt

```
Contexte : page {page} du site {domaine}.
Objectif : une FAQ construite sur les vraies questions reçues.

1. Récupère les requêtes de cette page sur 6 mois.
2. Isole celles qui sont des questions : soit elles commencent par un
   interrogatif (comment, pourquoi, combien, quel, quand, est-ce que),
   soit elles en ont la forme implicite (« prix installation X »).
3. Déduplique les reformulations d'une même question — garde la
   formulation la plus recherchée comme intitulé.
4. Écarte celles qui sont DÉJÀ traitées dans le corps de la page : une
   FAQ qui répète le contenu ne sert à rien.
5. Rédige des réponses courtes et AUTONOMES : 2 à 4 phrases,
   compréhensibles hors contexte. C'est ce format que ChatGPT et
   Perplexity citent.
6. Trie par impressions décroissantes et garde les 8 meilleures.

Rends le bloc FAQ rédigé en HTML sémantique, puis le JSON-LD FAQPage
correspondant, prêt à coller. Indique en face de chaque question son
volume d'impressions.

Ne jamais inventer un chiffre : si la donnée manque ou si le volume
est trop faible pour conclure, dis-le explicitement.
Indique toujours la période et le volume qui portent tes conclusions.
```

Règles communes : voir `../SKILL.md`.
