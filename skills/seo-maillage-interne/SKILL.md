---
name: seo-maillage-interne
description: >
  Conçoit et applique le maillage interne : détection des orphelines, flux
  d'autorité vers les pages qui convertissent, ancres optimisées, réduction de
  la profondeur, liens contextuels à poser page par page. Déclencher sur
  "maillage interne", "liens internes", "pages orphelines", "linking interne",
  "où mettre mes liens", "ancres", "flux de jus", "PageRank interne",
  "relier mes articles".
---

# Maillage interne — le levier le plus sous-estimé

C'est la seule variable de ranking que vous contrôlez à 100 %, qui ne coûte
rien, et qui produit un effet en 2-4 semaines. Et c'est celle que presque
personne ne travaille sérieusement.

## Étape 1 — Cartographier

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/crawl_site.py" <url> --exporter crawl.csv
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/internal_pagerank.py" crawl.csv
```

Vous obtenez par page : liens entrants internes, liens sortants, profondeur,
score d'autorité interne. Croisez avec GSC (impressions, position) et GA4
(conversions) — sans ces deux dimensions, vous optimisez à l'aveugle.

## Étape 2 — Les 5 diagnostics

### 1. Pages orphelines
Zéro lien interne entrant. Elles ne recevront jamais d'autorité.

Priorisez celles qui ont déjà des impressions : une orpheline à
2 000 impressions/mois qui reçoit 3 liens bien placés bouge en trois
semaines. C'est le gain le plus rapide de tout le SEO.

### 2. Pages qui convertissent et sont sous-liées
Croisez GA4 (conversions) avec le nombre de liens entrants. Le constat
habituel : la page « devis » reçoit 2 liens contextuels, la page « mentions
légales » en reçoit 400 (le footer).

Objectif : au moins **10 liens contextuels** vers chaque page prioritaire.
Contextuels, c'est-à-dire dans le corps du texte — un lien de footer ou de
menu ne transmet quasiment rien en comparaison.

### 3. Profondeur excessive
Toute page qui rapporte doit être à 3 clics maximum de la home. Au-delà de
4, elle est crawlée rarement et positionnée mal.

Le correctif passe par le maillage (ajouter des liens depuis des pages peu
profondes), pas par la réorganisation des URL — qui coûte bien plus cher.

### 4. Culs-de-sac
Pages sans lien sortant interne. Elles absorbent sans redistribuer, et
l'utilisateur n'a nulle part où aller. Fréquent sur les vieux articles.

Minimum : 2-3 liens sortants pertinents.

### 5. Ancres
- **Sur-optimisation** : la même ancre exacte répétée 40 fois vers la même
  page. Diversifiez.
- **Ancres vides** : « cliquez ici », « en savoir plus », « ce lien ». Elles
  ne transmettent aucun signal sémantique. Remplacez-les systématiquement.
- **Ancres génériques répétées** : « nos services » depuis 50 pages, sans
  variation.

## Étape 3 — Les règles d'un bon lien

| Règle | Pourquoi |
|-------|----------|
| **Contextuel avant tout** | Un lien dans un paragraphe pèse bien plus qu'un lien de bloc « articles liés » |
| **Ancre descriptive** | Elle dit à Google et au lecteur ce qu'il trouvera |
| **Ancre variée** | Exacte, partielle, longue traîne, marque — mélangez |
| **Haut de page** | Un lien dans les 30 % supérieurs est mieux valorisé |
| **Pertinence thématique** | Un lien entre deux sujets sans rapport ne sert à personne |
| **Quantité raisonnable** | 5-15 liens internes contextuels par page. 80 liens diluent tout |
| **Cohérence du silo** | Priorité aux liens intra-silo |

## Étape 4 — Le plan, exécutable ligne par ligne

Le livrable n'est pas une carte. C'est une liste d'actions :

| # | Depuis | Vers | Ancre | Où | Raison |
|---|--------|------|-------|-----|--------|
| 1 | /blog/fuite-eau | /services/plomberie | dépannage plomberie à Lyon | §2, après « appeler un professionnel » | Orpheline · 2 100 impressions |
| 2 | /blog/prix-chaudiere | /services/chauffage | installation de chaudière | intro | Page de conversion sous-liée |
| 3 | /services/plomberie | /blog/fuite-eau | que faire en cas de fuite | section interventions | Lien retour du silo |

Chaque ligne doit être applicable par quelqu'un qui ne réfléchit pas. Si
l'exécutant doit choisir où mettre le lien, le plan est incomplet.

## Étape 5 — Appliquer

**Mode autonomous + CMS branché** → application directe. Sauvegarde de
l'état d'origine avant chaque modification.

**Sinon** → le CSV, ligne par ligne. Comptez 2-3 minutes par lien à la main.

Rythme conseillé : **20 à 30 liens par semaine**. Poser 400 liens internes en
une journée sur un site qui n'en avait pas est un changement brutal. Étalez.

## Étape 6 — Mesurer

Enregistrez les positions de départ des pages ciblées. Reprenez à J+30.

L'effet typique d'un maillage bien fait : +3 à +8 positions sur les pages
qui passent de 0-2 à 10+ liens entrants contextuels. C'est mesurable, et
c'est gratuit.

## Le maillage à l'échelle

Sur un gros site, définissez des règles automatiques plutôt que des liens
individuels :

- Chaque article lie vers sa page catégorie (remontée d'autorité)
- Chaque page catégorie lie vers ses 10 articles les plus récents
- Bloc « articles liés » calculé par similarité sémantique, pas par date
- Fiche produit → catégorie parente + 4 produits proches
- Une page hub par silo, liée depuis la navigation principale

Attention : les blocs automatiques génèrent des liens de faible valeur. Ils
complètent les liens contextuels, ils ne les remplacent pas.

## Livrables

- `MAILLAGE.md` — diagnostic complet
- `liens-a-poser.csv` — le plan exécutable
- `orphelines.csv` — priorisées par impressions
- `autorite-interne.csv` — le PageRank interne par page
- `baseline-positions.json` — pour mesurer à J+30
