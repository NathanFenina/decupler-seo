---
name: seo-benchmark
description: >
  Avant de créer ou refondre une page, relève ce que font les 3 meilleures
  pages concurrentes sur sa requête, dans chaque langue du projet, et fixe la
  grille « faire mieux » : la page ne sort que si elle bat la meilleure sur au
  moins 5 axes. Déclencher dès qu'on crée, rédige ou refond une page, un
  outil, un comparatif, une offre, et sur "benchmark", "faire mieux que",
  "ce que font les autres", "meilleure page concurrente", "comparer à la
  concurrence sur cette page".
---

# Benchmark — faire mieux que la meilleure page

Règle d'or : **on ne publie rien sans avoir regardé la meilleure page
concurrente, et chaque page doit la battre objectivement.** « Aussi bien »
ne suffit pas : Google n'a aucune raison de remplacer une page par une autre
équivalente.

`seo-competitor-gap` compare des sites. Ce skill compare **une page à une
page**, juste avant de l'écrire.

## Quand

- Nouvelle page : guide, pilier, page locale, comparatif, outil, lead magnet
- Refonte d'une page ou d'un composant (hero, tableau, formulaire)
- Nouvelle offre ou nouveau CTA

## Procédure — 15 à 30 minutes par page

1. **SERP**, pour le mot-clé principal, **dans chaque langue du projet**
   (`decupler-seo.config.yml` → `projet.langues`) : top 5 organique et
   questions « Autres questions posées » (DataForSEO, Firecrawl, recherche web).
2. **Lire réellement les 3 meilleures pages** (Firecrawl) et relever :
   - angle et promesse, structure Hn, profondeur (étapes, coûts, délais)
   - données chiffrées, leur source et leur date
   - outils : tableau, calculateur, checklist, modèle, visuel
   - conversion : CTA, formulaire (quels champs), contact direct
   - réassurance : preuves, équipe, avis — et ce qui est vérifiable
   - SEO/GEO : title, meta, schema, FAQ, hreflang, fraîcheur affichée
3. **Remplir la grille** et viser au moins **5 axes gagnés** :

| Axe | Meilleure concurrente | Nous |
|---|---|---|
| Précision et fraîcheur des données (sources, date de mise à jour) | | |
| Couverture des questions (PAA, objections, coûts cachés) | | |
| Utilité concrète (tableau, simulateur, checklist, modèle) | | |
| Clarté (compris en 30 secondes, réponse en tête) | | |
| Conversion (CTA contextuel, contact direct, formulaire qualifiant) | | |
| Réassurance honnête (méthode, sources, engagements écrits) | | |
| Langue native dans chaque marché (pas de traduction brute) | | |
| Données structurées et citabilité IA (réponse directe, FAQ, schema) | | |

4. **Consigner** dans `recherche/benchmarks/<page>.md` : date, URL
   analysées, grille remplie, et les axes où l'on ne gagne pas — avec la
   raison. C'est ce fichier que la routine de fraîcheur relira dans six mois.

Moins de 5 axes gagnés → la page n'est pas prête. Dites-le, et dites ce
qui manque, plutôt que de publier une page « correcte ».

## Garde-fous

- **Ne jamais copier.** S'inspirer d'une structure, écrire mieux.
- **Aucune preuve fabriquée pour gagner l'axe réassurance** : ni faux avis,
  ni faux logos, ni compteur de clients inventé, ni certification supposée.
  La réassurance légitime vient de la transparence de méthode, des sources
  officielles citées, des engagements écrits et de l'expertise réelle. Une
  preuve inventée est une pratique commerciale trompeuse, et elle se détecte.
- Un chiffre relevé chez un concurrent n'est pas une source : remontez à la
  source officielle avant de l'utiliser.
