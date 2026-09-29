---
name: seo-serp-analysis
description: >
  Analyse une SERP en direct : qui ranke et pourquoi, intention dominante,
  features occupées (featured snippet, PAA, AI Overview, images, vidéos,
  local pack), format attendu, difficulté réelle. Déclencher sur "analyse la
  SERP", "qui ranke sur", "que sort Google sur", "featured snippet", "People
  Also Ask", "AI Overview", "quel format pour cette requête", "intention de
  recherche", "difficulté de ce mot-clé".
---

# Analyse de SERP — lire ce que Google a déjà décidé

La SERP est la réponse de Google à la question « qu'est-ce qu'un bon
résultat pour cette requête ». Elle est publique, gratuite et sans
ambiguïté. La lire évite d'écrire pendant six heures un guide de 3 000 mots
sur une requête où Google ne montre que des fiches produit.

## Étape 1 — Récupérer la SERP et lire le top

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/serp_concurrents.py" --mot "<requête>" --langue fr [--top 8] [--url <page du client>]
```

Une SERP DataForSEO (pays de la config) : top 10, **toutes les features**
(`item_types`), PAA dépliées d'un niveau, AI Overview chargé même quand
Google l'affiche en différé (extrait et sources citées), extrait optimisé,
recherches associées. Puis chaque page du top est lue : title, meta, plan
H1-H3, listes, tableaux, mots, FAQ, schémas, images, liens, dates, ton.
Coût : 0,002 à 0,004 $ ; la lecture des pages est gratuite (le repli
`--repli-dataforseo` pour les pages bloquées est facturé).

À défaut d'identifiants : une recherche en navigation privée sur le bon
domaine Google, et les pages lues avec Firecrawl.

## Étape 2 — L'intention dominante

Regardez les types de page du top 5, pas ce que vous croyez que les gens
veulent :

| Ce que montre le top 5 | Intention réelle | Ce que vous devez produire |
|------------------------|------------------|----------------------------|
| Articles de blog, guides | Informationnelle | Guide, tutoriel |
| Pages catégorie, produits | Transactionnelle | Page commerciale, pas un article |
| Comparatifs, « meilleurs X » | Commerciale | Comparatif avec tableau |
| Pages d'accueil de marques | Navigationnelle | Rien à faire ici |
| Mélange | Intention ambiguë | Page hybride, ou choisir un camp |

**Si le top 5 est composé de pages produit, écrire un article de blog est
une perte de temps** — quelle que soit sa qualité. C'est l'erreur la plus
coûteuse et la plus fréquente.

Cas particulier : une SERP mixte est une opportunité. Google hésite, ce qui
veut dire qu'un format bien exécuté peut s'y installer.

## Étape 3 — Les features, et ce qu'elles imposent

| Feature | Ce que ça signifie | Comment la prendre |
|---------|-------------------|--------------------|
| **AI Overview** | Le CTR organique chute. Être cité dedans devient l'objectif | Réponse directe de 40-60 mots, structure claire, données sourcées |
| **Featured snippet** | Position 0 prenable | Copier le format du snippet actuel : paragraphe (40-60 mots), liste, ou tableau |
| **People Also Ask** | Les sous-questions à couvrir | Chaque question PAA = un H2 ou une entrée de FAQ |
| **Pack local** | Requête locale | Sans fiche Google Business, l'organique seul plafonne |
| **Images / vidéos** | Format visuel attendu | Prévoyez des visuels originaux, ou une vidéo |
| **Shopping** | Requête d'achat | Page produit avec schema Product |
| **Discussions et forums** | Google veut de l'expérience vécue | Reddit et forums vous devancent — soyez présent là-bas aussi |
| **Sitelinks étendus** | Domaine dominant en place | Difficulté réelle plus élevée que le KD affiché |

Le bloc « Discussions et forums » est un signal fort : sur cette requête,
Google privilégie l'expérience de première main. Un contenu de marque
générique n'y a aucune chance.

## Étape 4 — Disséquer le top 3

Le rapport mesure déjà, pour chaque page : **longueur, plan Hn complet,
listes et tableaux, FAQ, schémas, date de mise à jour, façon d'ouvrir,
adresse au lecteur et longueur des phrases**. Et pour l'ensemble : la
fourchette de longueur (médiane → 3e quartile), les **sujets de H2
récurrents** (ce que Google attend), les sujets qu'une seule page traite,
les questions que **aucun titre du top** ne traite, et le champ sémantique
commun.

Restent à établir, par la lecture et les outils de liens :

- Type de domaine : marque, média, annuaire, forum, concurrent direct
- Autorité du domaine et **backlinks vers cette page précise**
- Éléments distinctifs : calculateur, vidéo, données propriétaires
- Signaux E-E-A-T : auteur identifié, credentials, expérience de terrain
- Répondent-ils dès la première phrase ? (`-contenus.md`)

Une mesure ne vaut que si la page a été lue : une page à 150 mots sur un
site éditorial est une page bloquée ou rendue en JavaScript, signalée comme
telle et exclue des statistiques — pas un concurrent faible.

Puis la synthèse en une phrase : *« Pour ranker ici, il faut un comparatif
d'au moins 8 solutions, avec un tableau, un auteur identifié et environ
15 domaines référents. »*

## Étape 5 — Difficulté réelle

Le KD des outils est une estimation générique. Lisez la SERP :

**Signes que c'est prenable** — présence d'annuaires ou de contenus faibles
dans le top 10, pages non mises à jour depuis 2+ ans, top 10 hétérogène,
aucun acteur avec une page vraiment dédiée à la requête.

**Signes qu'il faut passer votre chemin** — top 10 entièrement composé de
marques établies, sitelinks étendus sur le premier résultat, pages avec
100+ domaines référents chacune, SERP figée depuis longtemps.

Confrontez toujours à **votre** autorité, pas dans l'absolu.

## Étape 6 — La décision

Concluez par une recommandation nette :

- ✅ **Y aller** — format à produire, angle différenciant, effort estimé,
  ce qu'il faudra en liens
- ⚠️ **Y aller autrement** — la requête frontale est hors de portée, voici
  la variante longue traîne à viser d'abord
- ❌ **Passer** — pourquoi, et sur quoi mettre l'effort à la place

## Livrables

- `recherche/serp-<slug>-<date>.md` — les mesures (produit par le script)
- `recherche/serp-<slug>-<date>-contenus.md` — le contenu structuré du top
- La décision de l'étape 6, en tête du rapport ou dans le brief
- Les questions PAA, exploitables directement en FAQ ou en plan Hn
