---
name: seo-keyword-research
description: >
  Recherche de mots-clés complète : expansion sémantique, volumes, difficulté,
  classification par intention, risque zero-click IA, opportunité GEO, et
  arbitrage créer / optimiser / ignorer. Déclencher sur "mots-clés",
  "keyword research", "recherche de mots-clés", "sur quoi me positionner",
  "volume de recherche", "intention de recherche", "quels sujets traiter",
  "champ sémantique", "requêtes", "je cherche des idées de contenu".
---

# Recherche de mots-clés — arbitrer, pas collectionner

Une liste de 800 mots-clés n'est pas un livrable. C'est une façon de ne rien
décider. Le livrable, c'est **20 requêtes qu'on va travailler et la raison
pour laquelle on ignore les autres**.

## Étape 1 — Le point de départ

Trois sources, dans cet ordre de fiabilité :

1. **Search Console** — ce sur quoi vous êtes déjà vu. La donnée la plus
   fiable qui existe, parce qu'elle est vraie pour *votre* site. Les requêtes
   à impressions et sans clic sont les plus rentables.
2. **Vos concurrents** — leurs mots-clés organiques (Semrush, Ahrefs). Ils
   ont déjà fait le travail de validation du marché.
3. **L'expansion** — Ubersuggest, suggestions Google, DataForSEO,
   People Also Ask, Reddit.

Reddit mérite un mot : c'est la meilleure source de **vocabulaire réel**.
Les gens y écrivent leurs problèmes avec leurs mots, pas avec les vôtres.
Un mot-clé issu d'un thread Reddit convertit mieux qu'un mot-clé issu d'un
outil.

## Étape 2 — Enrichir

Pour chaque requête, via DataForSEO / Semrush :
volume mensuel, tendance 12 mois, difficulté, CPC (proxy de valeur
commerciale), features SERP présentes, présence d'un AI Overview.

Le CPC est un signal sous-utilisé : un mot-clé à 12 € de CPC vaut de l'argent
même à 90 recherches/mois. Un mot-clé à 0,10 € et 8 000 recherches/mois n'en
vaut souvent aucun.

## Étape 3 — Classer par intention

| Intention | Marqueurs | Ce qu'il faut produire |
|-----------|-----------|------------------------|
| **Informationnelle** | comment, pourquoi, qu'est-ce que, guide | Guide, tutoriel, définition |
| **Commerciale** | meilleur, comparatif, avis, alternative, vs | Comparatif, test, page alternative |
| **Transactionnelle** | acheter, prix, tarif, devis, près de moi | Page produit, service, devis |
| **Navigationnelle** | marque + terme | Page dédiée, ou rien |

Et sur le parcours d'achat : Découverte → Considération → Décision.

Erreur classique : produire uniquement de l'informationnel parce que c'est
là qu'est le volume, puis s'étonner que le trafic ne convertisse pas.
Visez un équilibre 40 / 40 / 20.

## Étape 4 — Le risque zero-click IA (nouveau, et déterminant)

En 2026, une part croissante des requêtes informationnelles reçoit une
réponse directe dans l'AI Overview. Vous êtes cité, on ne clique pas.

| Risque | Type de requête | Décision |
|--------|-----------------|----------|
| 🔴 Élevé | Fait simple : « qu'est-ce que le SEO », « capitale du Pérou », conversions, définitions | **Ne créez pas de page dédiée.** Traitez-le en section d'une page plus large |
| 🟡 Moyen | Procédural, multi-dimensionnel : « comment choisir un CRM » | Créez, mais avec de la profondeur que l'IA ne peut pas résumer |
| 🟢 Faible | Local, temps réel, avis, données propriétaires, comparaison nuancée, transactionnel | **Créez en priorité.** Le clic reste |

Ce filtre change radicalement une stratégie de contenu. Un plan éditorial de
2023 rempli de « qu'est-ce que X » est aujourd'hui un plan à trafic nul.

## Étape 5 — L'opportunité GEO

Un mot-clé peut avoir peu de clics et beaucoup de valeur, s'il vous fait
citer par les moteurs IA auprès d'acheteurs. Notez chaque requête de 1 à 5 :

- Est-ce une question qu'un décideur pose à ChatGPT avant d'acheter ?
- La réponse actuelle des LLM est-elle mauvaise ou incomplète ?
- Avez-vous une donnée propriétaire à apporter ?

Un 5/5 en GEO avec 40 recherches/mois peut valoir plus qu'un 3 000/mois
informationnel saturé.

## Étape 6 — Décider

Trois piles, et on assume la troisième :

**🔴 À FAIRE MAINTENANT** — bonne intention, difficulté atteignable,
zero-click faible, valeur business réelle. Maximum 20 lignes.

**🟡 À FAIRE AVEC UN ANGLE** — le volume est là mais la SERP est saturée ou
le zero-click est élevé. Précisez l'angle qui vous rend citable : donnée
originale, format différent, niche plus étroite.

**⚫ À IGNORER** — trop difficile pour votre autorité actuelle, hors
proposition de valeur, ou tellement zero-click qu'il n'y a rien à gagner.
**Dites pourquoi.** C'est la partie la plus utile du livrable.

Sur la difficulté : comparez au Domain Rating de votre site, pas dans
l'absolu. Un KD 40 est infranchissable à DR 8 et facile à DR 65.

## Étape 7 — Regrouper en clusters

Ne créez pas une page par mot-clé. Regroupez les requêtes qui partagent la
même intention et la même SERP (si le top 10 est identique à 60 %, c'est la
même page).

Par cluster : la requête principale, les 5-15 secondaires, la page cible
(existante ou à créer), le type de page, la priorité.

## Livrables

- `MOTS-CLES.md` — les 3 piles, avec justification
- `mots-cles.csv` — tableau complet : requête, volume, KD, CPC, intention,
  parcours, zero-click, GEO, cluster, décision
- `CLUSTERS.md` — l'architecture éditoriale qui en découle

Enchaînez : `/seo cocon` pour l'architecture, `/seo brief` pour produire.
