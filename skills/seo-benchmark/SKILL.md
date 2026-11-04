---
name: seo-benchmark
description: >
  Avant de créer ou refondre une page, relève les 3 meilleures pages
  concurrentes sur sa requête et fixe la grille « faire mieux » (battre la
  meilleure sur au moins 5 axes). Déclencher sur « benchmark de page », «
  faire mieux que », « meilleure page concurrente », et à chaque création de
  page. Pas pour une analyse de concurrents à l'échelle du site →
  seo-competitor-gap.
---

# Benchmark — faire mieux que la meilleure page

Règle d'or : **on ne publie rien sans avoir regardé la meilleure page
concurrente, et chaque page doit la battre objectivement.** « Aussi bien »
ne suffit pas : Google n'a aucune raison de remplacer une page par une autre
équivalente.

`seo-competitor-gap` compare des sites. Ce skill compare **une page à une
page**, juste avant de l'écrire.


**Sans projet configuré, sans données ni accès** (dossier vide, pas de
Search Console, pas d'outil web) : ne vous arrêtez pas sur une question.
Livrez tout de suite ce qui ne dépend pas des données — la méthode appliquée
au cas, un exemple rempli, le livrable type avec des emplacements
`[à compléter : …]` — puis, en fin de réponse, la liste de ce qu'il faut
fournir pour la version chiffrée. Aucun chiffre inventé.

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

4. **Consigner** dans `recherche/benchmarks/<page>.md` (ou le dossier que
   désigne `memoire/decisions.md`) : date, URL analysées, grille remplie, et
   les axes où l'on ne gagne pas — avec la raison. C'est ce fichier que la routine de fraîcheur relira dans six mois.

Moins de 5 axes gagnés → la page n'est pas prête. Dites-le, et dites ce
qui manque, plutôt que de publier une page « correcte ».

## Veille mensuelle — le benchmark ne s'arrête pas à la publication

Le top 5 bouge (relevés de projets : aucun domaine commun entre deux tops pris à quelques semaines
d'écart). Le premier cycle de chaque mois, sur les 10 pages qui rapportent le plus
(`projet.pages_prioritaires`), on relève de nouveau le top 5 du mot-clé et on remplit une grille
par page concurrente dans `recherche/veille/<AAAA-MM>.md` :

| Axe | Ce qu'on note |
|---|---|
| Design | structure du hero, blocs visuels (carte, comparatif, process, simulateur), photos ou illustrations, rythme des sections |
| UX | sommaire et ancres, lisibilité mobile, formulaire, téléphone cliquable, temps pour trouver le prix ou le contact |
| CRO | nombre de CTA, places, libellés, preuves près des CTA (avis, logos, chiffres), offres ou formules affichées, outil gratuit en appel |
| SEO | title, H1, plan H2, longueur, FAQ, questions « Autres questions posées » traitées, maillage vers les pages sœurs |
| Technique | types JSON-LD, FAQPage, vitesse ressentie, poids et `alt` des images, canonique |

Chaque bonne idée entre, datée et avec l'URL source, dans le skill de rédaction du projet
(`.claude/skills/projet-*`) : c'est ainsi que le skill s'améliore de mois en mois. Une idée qui demande
un nouveau bloc devient une action de la page de suivi ; une idée déjà mieux appliquée chez nous ne
s'ajoute pas. Le style et les exemples restent dans le dépôt du projet, jamais dans la méthode.

## Garde-fous

- **Ne jamais copier.** S'inspirer d'une structure, écrire mieux.
- **Aucune preuve fabriquée pour gagner l'axe réassurance** : ni faux avis,
  ni faux logos, ni compteur de clients inventé, ni certification supposée.
  La réassurance légitime vient de la transparence de méthode, des sources
  officielles citées, des engagements écrits et de l'expertise réelle. Une
  preuve inventée est une pratique commerciale trompeuse, et elle se détecte.
- Un chiffre relevé chez un concurrent n'est pas une source : remontez à la
  source officielle avant de l'utiliser.
