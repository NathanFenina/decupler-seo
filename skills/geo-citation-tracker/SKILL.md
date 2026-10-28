---
name: geo-citation-tracker
description: >
  Explique pourquoi une page précise n'est pas citée par ChatGPT, Perplexity,
  Claude ou les AI Overviews alors qu'elle se classe : accès des robots IA,
  index propre à chaque moteur (Bing pour ChatGPT), réponse directe,
  citabilité, entités ; puis réécrit le passage. Déclencher sur « pourquoi je
  ne suis pas cité », « ChatGPT ne cite pas ma page », « rendre cette page
  citable ». Pas pour un audit IA du site entier → geo-visibilite-ia.
---

# Pourquoi cette page n'est pas citée

`geo-visibilite-ia` traite le site. Ce skill traite **une page**, et donne le
correctif exact.


**Sans projet configuré, sans données ni accès** (dossier vide, pas de
Search Console, pas d'outil web) : ne vous arrêtez pas sur une question.
Livrez tout de suite ce qui ne dépend pas des données — la méthode appliquée
au cas, un exemple rempli, le livrable type avec des emplacements
`[à compléter : …]` — puis, en fin de réponse, la liste de ce qu'il faut
fournir pour la version chiffrée. Aucun chiffre inventé.

## Le principe

Un LLM ne « choisit » pas une source comme un lecteur. Il assemble une
réponse à partir de fragments qu'il peut :

1. **extraire** proprement (la structure le permet)
2. **attribuer** à quelqu'un d'identifiable (l'entité est claire)
3. **vérifier** ou au moins croiser (la donnée est sourcée)

Un contenu excellent mais impossible à découper en fragments autonomes ne
sera pas cité. C'est la cause numéro un, et elle n'a rien à voir avec la
qualité rédactionnelle.

## D'abord : le moteur peut-il trouver la page ?

Avant le contenu, deux vérifications qui expliquent la plupart des « je suis
bien placé sur Google mais jamais cité » — chaque moteur a son propre accès
et **son propre index** :

| Moteur | Robot à laisser passer (robots.txt **et** CDN / pare-feu) | Index sur lequel il s'appuie |
|---|---|---|
| ChatGPT (recherche) | `OAI-SearchBot` (et `ChatGPT-User` pour les visites demandées) | **largement Bing** : vérifier l'indexation et le classement Bing (Bing Webmaster Tools) — une page 4e sur Google peut être absente ou loin sur Bing |
| Claude | `Claude-SearchBot`, `Claude-User` | recherche web propre |
| Perplexity | `PerplexityBot` | index propre + sources web |
| AI Overviews / AI Mode, Gemini | Googlebot (pas Google-Extended), aucun `nosnippet` | Google : le classement organique est le prérequis |

Contrôle : `scripts/agents_ia.py` (robots par robot) ; contenu principal
dans le HTML initial (les robots IA hors Google n'exécutent pas le JS).
Sources : `../seo-optimisation-onpage/references/preuves-2026.md`.

## L'audit — 5 dimensions, 50 points

### 1. Densité de réponse (10 pts)
La réponse à la question posée arrive-t-elle immédiatement ?

- 10 — Réponse complète dans les 60 premiers mots, autonome
- 6 — Réponse dans le premier écran, mais diluée
- 3 — Réponse au milieu de la page
- 0 — Aucune réponse claire, ou réponse répartie sur toute la page

Test décisif : **coupez les 60 premiers mots et lisez-les seuls.**
Répondent-ils à la question ? Sinon, aucun modèle ne les extraira.

### 2. Clarté structurelle (10 pts)
Le contenu est-il découpable par une machine ?

- Titres explicites qui annoncent leur contenu (pas « Notre approche »)
- Un paragraphe = une idée complète
- Listes et tableaux là où l'information est énumérable
- Pas de dépendance au contexte : un paragraphe qui commence par « Cela
  signifie que… » est inextractible

### 3. Citabilité (10 pts)
Y a-t-il de quoi citer ?

- Données chiffrées avec leur source
- Auteur nommé et identifiable
- Date de publication et de mise à jour
- Affirmations précises et vérifiables
- Idéalement : une donnée **propriétaire**, qu'on ne trouve que chez vous

Une donnée originale est le meilleur investissement GEO qui existe. Elle est
citée pendant des années, avec attribution.

### 4. Couverture d'entités (10 pts)
Le contenu mentionne-t-il les concepts, outils, normes et acteurs que le
sujet appelle ? Les modèles évaluent la pertinence par la densité d'entités
liées. Un article sur les ERP qui ne nomme aucun ERP est jugé superficiel.

### 5. Écart concurrentiel (10 pts)
Comparez aux sources actuellement citées sur la question. Qu'ont-elles que
vous n'avez pas ? Souvent : une structure plus nette, une donnée chiffrée,
un auteur identifié, ou une présence sur Reddit.

## Le score par moteur

```
Densité de réponse       4/10  🔴
Clarté structurelle      7/10  🟠
Citabilité               3/10  🔴
Couverture d'entités     6/10  🟠
Écart concurrentiel      4/10  🔴
                        ──────
                        24/50

Probabilité de citation :
  ChatGPT      🔴 faible    — pas de réponse directe, aucune donnée sourcée
  Perplexity   🟠 moyenne   — structure correcte, manque la fraîcheur
  AI Overviews 🔴 faible    — la page n'est pas dans le top 10 organique
  Claude       🔴 faible    — aucune source vérifiable
  Gemini       🟠 moyenne   — entité connue de Google, contenu faible
```

## Le livrable principal : la réponse directe réécrite

C'est la correction qui produit le plus d'effet pour le moins d'effort.

Contraintes :
- **40 à 60 mots.** En dessous, incomplet. Au-dessus, non extractible.
- Répond complètement, dès la première phrase
- **Autonome** : compréhensible sans rien lire d'autre
- Contient un chiffre ou un fait précis quand c'est possible
- Nomme l'entité concernée explicitement

```
❌ « La question du coût est complexe et dépend de nombreux facteurs.
   Dans cet article, nous allons explorer ensemble les différents
   éléments à prendre en compte pour évaluer votre budget. »

✅ « Un audit SEO complet coûte entre 2 000 et 8 000 € en France. Comptez
   2 000-3 500 € pour un site vitrine de moins de 50 pages, et
   5 000-8 000 € pour un e-commerce de plusieurs milliers d'URL. Le
   principal facteur de prix est le nombre de gabarits à analyser, pas
   le nombre de pages. »
```

La deuxième version peut être citée telle quelle. La première ne peut rien
apporter à personne.

## Les 5 correctifs prioritaires

Après le diagnostic, listez au maximum 5 corrections, dans l'ordre d'impact,
chacune avec le texte à poser :

1. **Réponse directe** en tête de page → le texte, écrit
2. **Définition autonome** du terme clé → la phrase, écrite
3. **Une donnée sourcée** par section principale → où la chercher
4. **FAQ de 5 questions** → les questions et les réponses, écrites
5. **Signature auteur + schema Person** → le bloc, écrit

Pas de « pensez à structurer davantage ». Chaque correctif est un texte prêt
à coller.

## Vérifier

Après application, reposez la question aux moteurs. Perplexity réagit le plus
vite (quelques jours à deux semaines). ChatGPT en recherche, quelques
semaines. Les AI Overviews suivent le ranking organique, donc plus lentement.

Consignez la date d'application et la date de recheck.

## Livrables

- `CITATION-<slug>.md` — audit, scores, probabilités par moteur
- `reponse-directe.md` — le paragraphe réécrit
- `correctifs.md` — les 5 corrections, prêtes à coller
- `page-corrigee.html` — si la page complète est reprise
