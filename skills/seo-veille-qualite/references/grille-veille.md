# Grille de veille qualité : 100 points

Chaque critère vaut **0** (absent ou faux), **1** (partiel) ou **2** (rempli),
sauf mention. Une note sans preuve d'une ligne vaut 0. ★ = bloquant : un ★ à 0
met la page en tête des corrections, quel que soit son total.

## A. Intention et SERP actuelle (20)

| # | Critère | Points |
|---|---|---|
| A1 ★ | Le format de la page (guide, comparatif, outil, liste, service) correspond à ce que le top 5 montre **ce mois-ci** | 0/2/4 |
| A2 ★ | L'intention dominante est servie dès le premier écran (réponse, prix, délai ou action visible sans défiler) | 0/2/4 |
| A3 ★ | Aucune autre page du site n'a pris le mot-clé (Search Console : une seule page du site sur la requête) | 0/2/4 |
| A4 | Les nouveautés de la SERP depuis le dernier relevé (nouvel entrant, AI Overview, PAA nouvelles) sont prises en compte | 0/2/4 |
| A5 | Title et H1 alignés sur la formulation que Google montre en tête, sans copier un concurrent | 0/2/4 |

## B. Valeur et gap sémantique (20)

| # | Critère | Points |
|---|---|---|
| B1 ★ | Entités du top 5 couvertes : part des entités relevées (argument `--entites` d'`onpage_score.py`) présentes dans la page. 90 % et plus = 6, 70 % = 4, 50 % = 2 | 0-6 |
| B2 | Questions PAA et questions des réponses IA couvertes (liste cochée) | 0/2/4 |
| B3 | Information gain : au moins 3 éléments que le top 5 n'a pas (cas réel, chiffre sourcé, tableau, piège, coût poste par poste) | 0/3/6 |
| B4 | Chaque section apporte un fait, une règle, un exemple ou un conseil ; aucune section de remplissage | 0/2/4 |

## C. Concurrence (20)

| # | Critère | Points |
|---|---|---|
| C1 ★ | La page bat encore la meilleure concurrente sur au moins 5 axes de la grille « faire mieux » (`seo-benchmark`), relus ce mois-ci. 5 axes = 10, 4 = 8, 3 = 6, 2 = 4, 1 = 2 | 0-10 |
| C2 | Ce que le concurrent qui a le plus progressé a ajouté depuis le dernier relevé est identifié et couvert ou volontairement écarté (raison écrite) | 0/2/5 |
| C3 | Profondeur au niveau du marché : longueur utile ≥ médiane du top 3, sans remplissage, ou format plus court justifié | 0/2/5 |

## D. GEO (20)

| # | Critère | Points |
|---|---|---|
| D1 ★ | Réponse directe de 40 à 80 mots au prompt principal, autonome et citable, en tête de page ou de section | 0/3/6 |
| D2 | Faits clés écrits en triplets explicites (sujet, prédicat, objet), une seule valeur par fait sur le site | 0/2/4 |
| D3 | Citée par au moins un moteur IA sur le prompt principal (relevé du mois) ; 2 moteurs ou plus = 6 | 0/3/6 |
| D4 | Données structurées valides et cohérentes avec le texte (`schema_validate.py`) | 0/2/4 |

## E. On-page et confiance (20)

| # | Critère | Points |
|---|---|---|
| E1 | Score `onpage_score.py` divisé par 10, arrondi (92 → 9) | 0-10 |
| E2 ★ | Chaque chiffre de la page vient de `memoire/faits.md`, daté ; aucune contradiction avec une autre page | 0/3/6 |
| E3 | Fraîcheur : page relue ou mise à jour depuis moins de 6 mois, date de mise à jour visible | 0/2/4 |

## Lecture du total

- **85 et plus** : page de référence ; on la défend (veille sur les concurrents).
- **70 à 84** : corrections ciblées sur le bloc le plus faible.
- **Moins de 70**, ou un ★ à 0 : page prioritaire du mois.
