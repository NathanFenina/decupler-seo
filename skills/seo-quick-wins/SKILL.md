---
name: seo-quick-wins
description: >
  Identifie dans Search Console les pages en position 5-20 avec de fortes
  impressions, analyse l'écart avec le top 3, et produit les corrections
  exactes pour les faire monter. Le meilleur rapport effort/résultat du SEO.
  Déclencher sur "quick wins", "gains rapides", "pages à rattraper",
  "positions 8-15", "qu'est-ce que je corrige en premier", "j'ai peu de
  temps", "actions rentables", "améliorer mon trafic rapidement",
  "opportunités GSC", ou un export Search Console collé.
---

# Quick wins — la chaîne la plus rentable du dispositif

Une page en position 12 a déjà tout : Google la connaît, la juge pertinente,
la montre. Il manque un cran. Passer de 12 à 6 multiplie le clic par 4-6.
Créer une page neuve prend 3 mois pour un résultat incertain.

**Faites toujours ça avant d'écrire quoi que ce soit de nouveau.**

## Étape 1 — Extraire la donnée (1 min)

Via le MCP Search Console, sur **90 jours glissants** :

```
dimensions : page + query
métriques  : impressions, clics, CTR, position
filtre     : position entre 4 et 20
tri        : impressions décroissantes
```

Sans MCP : Search Console → Résultats de recherche → exporter en CSV, puis
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gsc_analyse.py" export.csv`.

## Étape 2 — Trier en 4 paquets

Ne traitez pas tout pareil. Le diagnostic change selon la case :

| Position | CTR | Diagnostic | Correctif |
|----------|-----|------------|-----------|
| 4-10 | **bas** vs attendu | Problème de **snippet**, pas de contenu | Réécrire title + meta. 30 min, effet sous 2 semaines. |
| 4-10 | normal | Presque là | Renforcer le contenu, ajouter des liens internes |
| 11-20 | tout CTR | Contenu insuffisant vs top 3 | Combler l'écart éditorial |
| 4-20 | plusieurs URL sur la même requête | **Cannibalisation** | Fusionner ou différencier |

CTR moyen attendu par position (repère, ordre de grandeur) :
1 → 27 % · 2 → 15 % · 3 → 11 % · 4 → 8 % · 5 → 6 % · 6-10 → 2-5 % ·
11-20 → < 1,5 %. Un CTR à moitié de l'attendu = le snippet est le problème.

Attention : les AI Overviews écrasent le CTR de toutes les positions sur les
requêtes informationnelles. Comparez à vos propres pages, pas à la table.

## Étape 3 — Chiffrer le potentiel

Pour chaque page :

```
clics_potentiels = impressions × CTR_position_cible
gain             = clics_potentiels − clics_actuels
```

Puis, si GA4 est branché, monétisez : `gain × taux_conversion × panier`.
Un plan chiffré en euros se fait valider ; un plan chiffré en positions non.

**Gardez les 10 premières lignes.** Pas 40. Un plan de 40 actions n'est
jamais exécuté.

## Étape 4 — Analyser l'écart avec le top 3

Pour chaque page retenue, sur sa requête principale :

1. SERP live (DataForSEO) → les 3 premiers résultats
2. Scraper chacun (Firecrawl) → plan Hn, longueur, format, angles
3. Comparer avec votre page :
   - Quels sous-sujets couvrent-ils que vous ne couvrez pas ?
   - Quel format ? (guide, comparatif, outil, vidéo, tableau)
   - Répondent-ils plus vite en haut de page ?
   - Ont-ils des données propriétaires que vous n'avez pas ?
   - Quelles features SERP occupent-ils ? (PAA, featured snippet, image)

**Ne réécrivez pas la page.** Identifiez les 2-3 blocs manquants et
ajoutez-les. Une réécriture complète remet le compteur à zéro et fait
souvent perdre des positions pendant plusieurs semaines.

## Étape 5 — Produire les corrections

Par page, un bloc directement exploitable :

```markdown
## https://exemple.com/page-cible

**État** : position 11,4 · 3 200 impressions · 41 clics · CTR 1,3 %
**Potentiel** : position 6 → ~190 clics/mois · +149 clics · ~4 400 € /an
**Diagnostic** : contenu insuffisant sur 2 sous-sujets + title générique

### Title (à remplacer)
Avant : Nos services de plomberie
Après  : Plombier à Lyon : dépannage en 2 h, devis gratuit — 24/7
         (58 car., mot-clé en tête, promesse chiffrée)

### Meta description (à remplacer)
[texte de 155 car.]

### Sections à ajouter
1. **H2 : Combien coûte un dépannage plomberie à Lyon ?**
   Les 3 premiers ont tous un tableau de prix. Vous n'en avez pas.
   → tableau : intervention / fourchette / délai
2. **H2 : Que faire en attendant le plombier ?**
   Présent dans 2 PAA sur cette requête.
   → 5 gestes, un paragraphe chacun

### Liens internes à ajouter
- Depuis /blog/fuite-eau-que-faire → ancre « dépannage plomberie Lyon »
- Depuis /tarifs → ancre « nos interventions à Lyon »

### Vérification
Reprendre la position dans GSC à J+21.
```

## Étape 6 — Appliquer et suivre

Si le CMS est branché et le mode autonomous actif : appliquer les titles et
metas directement (`/seo publish`), les sections de contenu en brouillon.

Puis **inscrire dans le suivi** : la position de départ, la date de la
modification, la position cible. Sans point de départ enregistré, vous ne
saurez jamais si ça a marché. Si Notion est branché, une ligne par page dans
la base Roadmap.

## Cadence

Mensuelle. Les pages changent de position, de nouvelles opportunités
apparaissent, et vos corrections du mois dernier ont eu le temps de produire
leur effet. `/loop 30d /seo quickwins` si vous voulez l'automatiser.

## Livrables

- `QUICK-WINS.md` — le plan chiffré, 10 pages max
- `quick-wins.csv` — pour partager ou suivre
- `baseline.json` — positions de départ, pour mesurer dans 3 semaines
