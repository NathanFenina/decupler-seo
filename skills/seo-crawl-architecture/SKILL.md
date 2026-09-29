---
name: seo-crawl-architecture
description: >
  Crawle un site et en cartographie l'architecture : profondeur, silos, pages
  orphelines, culs-de-sac, distribution de l'autorité, budget de crawl.
  Produit une carte exploitable et un plan de restructuration. Déclencher sur
  "crawl", "crawler mon site", "architecture", "arborescence", "pages
  orphelines", "profondeur de clic", "structure du site", "budget de crawl",
  "cartographie", "combien de pages j'ai".
---

# Crawl et architecture

L'architecture est le squelette. Un site avec du bon contenu mal structuré
sous-performe systématiquement — et c'est invisible page par page.

## Le crawl

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/crawl_site.py" <url> --max 500 --delai 1000 --respecter-robots
```

Collecte par URL : code HTTP, profondeur depuis la home, title, meta, Hn,
nombre de mots, liens entrants internes, liens sortants, canonical, statut
d'indexabilité, temps de réponse, poids.

Sur un site de plus de 500 pages, **échantillonnez par template** plutôt que
d'essayer de tout prendre : 30 fiches produit, 20 catégories, 30 articles.
Les problèmes d'architecture sont des problèmes de gabarit, pas de page.

## Les 6 diagnostics

### 1. Profondeur de clic
Distance depuis la home en nombre de clics.

| Profondeur | Verdict |
|------------|---------|
| 0-2 | Idéal — crawlé souvent, bien positionné |
| 3 | Acceptable |
| 4 | Crawl ralenti, autorité diluée |
| 5+ | Souvent ignoré par Google |

Une page qui rapporte de l'argent ne doit jamais être à plus de 3 clics.
Si c'est le cas, la corriger passe par le maillage, pas par l'URL.

### 2. Pages orphelines
Aucun lien interne entrant. Elles existent dans le sitemap, parfois dans
l'index, mais ne reçoivent aucune autorité. C'est **le gisement le plus
rentable et le plus fréquemment ignoré** : une page orpheline qui reçoit
3 liens internes bien placés bouge en 2-3 semaines.

Croisez avec GSC : une orpheline qui reçoit déjà des impressions est une
priorité absolue.

### 3. Culs-de-sac
Pages sans lien sortant interne. Elles absorbent l'autorité sans la
redistribuer, et l'utilisateur n'a nulle part où aller. Fréquent sur les
articles de blog anciens.

### 4. Distribution de l'autorité
Calculez un PageRank interne simplifié
(`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/internal_pagerank.py" crawl.csv`) et confrontez-le aux
`pages_prioritaires` de la config.

Le constat classique : la page « Mentions légales » reçoit 400 liens (le
footer) et la page qui vend en reçoit 6. Corrigez le déséquilibre.

### 5. Silos et cohérence thématique
Les pages d'un même sujet se lient-elles entre elles ? Un silo bien formé
concentre la pertinence. Un maillage aléatoire la dissout.

Repérez les liens transversaux inutiles : un lien depuis un article de
recettes vers une page de plomberie n'aide personne.

### 6. Budget de crawl
Sur un gros site : quelles URL consomment le crawl sans rien rapporter ?
Facettes, paramètres de tri, pagination infinie, résultats de recherche
interne, versions imprimables. Chaque URL inutile crawlée est une URL utile
non crawlée.

## La carte

Produisez une représentation lisible, pas un graphe illisible :

```
Accueil (profondeur 0)
├── /services/ ......................... 12 liens entrants · P1
│   ├── /services/plomberie/ ........... 8 · P2 · ⚠ 0 lien vers /devis
│   └── /services/chauffage/ ........... 6 · P2
├── /blog/ ............................. 45 · P1
│   ├── /blog/fuite-eau/ ............... 3 · P2 · 890 impressions
│   └── /blog/prix-chaudiere/ .......... 0 · P3 · 🔴 ORPHELINE · 2 100 impressions
└── /contact/ .......................... 340 · P1 (footer)

🔴 3 orphelines dont 1 à fort trafic potentiel
🟠 8 pages à profondeur ≥ 4
🟠 /devis ne reçoit que 2 liens internes (page de conversion)
```

## Plan de restructuration

Par ordre d'impact :

1. **Orphelines à impressions** → 3 liens contextuels chacune, depuis des
   pages thématiquement proches
2. **Pages prioritaires sous-liées** → remonter à 10+ liens entrants
3. **Profondeur > 4** → créer des passerelles depuis les pages hub
4. **Culs-de-sac** → 2-3 liens sortants pertinents
5. **Gaspillage de crawl** → règles robots + canonicals

Chaque action précise : depuis quelle page, vers quelle page, avec quelle
ancre. Un plan de maillage sans les ancres n'est pas exécutable.

## Livrables

- `ARCHITECTURE.md` — carte + diagnostics
- `crawl.csv` — inventaire complet
- `orphelines.csv` — priorisées par impressions GSC
- `PLAN-MAILLAGE.md` — les liens à créer, un par ligne

Enchaînez sur `/seo maillage` pour l'exécution.
