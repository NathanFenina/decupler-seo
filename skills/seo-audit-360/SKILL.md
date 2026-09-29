---
name: seo-audit-360
description: >
  Audit SEO complet d'un site : crawl, technique, contenu, E-E-A-T, schema,
  performance, maillage, visibilité IA. Orchestre les agents spécialisés en
  parallèle, agrège en un score de santé /100 et sort un plan d'action
  priorisé par impact business. Déclencher sur "audit", "audit complet",
  "audite mon site", "analyse mon site", "checkup SEO", "bilan SEO",
  "diagnostic", "état des lieux", "qu'est-ce qui cloche sur mon site",
  ou une URL de domaine seule sans autre consigne.
---

# Audit 360 — le point d'entrée de tout

Vous êtes le chef d'orchestre. Vous ne faites pas l'analyse vous-même : vous
collectez les faits, vous déléguez aux spécialistes, vous agrégez, vous
priorisez. Ce qui distingue un bon audit d'un mauvais n'est pas le nombre de
problèmes trouvés, c'est **l'ordre dans lequel on les corrige**.

## Phase 0 — Cadrage (2 min)

1. Lire `./decupler-seo.config.yml` du projet → section `projet`. S'il n'existe pas,
   lancer d'abord `seo-onboarding`.
2. `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py" --json` → savoir avec quoi on travaille.
3. Récupérer la page d'accueil : `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_page.py" <url>`.
4. **Détecter le type de business** depuis la home. Ça change tout le reste :

| Signaux détectés | Type | Ce qu'on regarde en priorité |
|------------------|------|------------------------------|
| Panier, prix, fiches produit | E-commerce | Facettes, canonicals, schema Product, pagination |
| Essai gratuit, tarifs mensuels, docs | SaaS | Pages comparatives, intégrations, TOFU/BOFU |
| Adresse, horaires, téléphone | Local | GBP, NAP, pages ville, schema LocalBusiness |
| Flux d'articles daté, auteurs | Média | Fraîcheur, silos, Discover, schema Article |
| Prestations, devis, références | Services | Pages métier, preuves, E-E-A-T, conversion |

Un audit e-commerce qui parle de fraîcheur éditoriale est un audit raté.

## Phase 1 — Crawl (5-10 min)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/crawl_site.py" <url> --max 500 --respecter-robots
```

Sort : inventaire des URL, codes HTTP, profondeur, titres, metas, Hn,
maillage entrant/sortant, poids, temps de réponse.

Garde-fous : 500 pages max, 1 req/s, robots.txt respecté. Sur un très gros
site, échantillonnez par template plutôt que d'essayer de tout crawler —
50 pages bien choisies valent mieux que 500 au hasard.

## Phase 2 — Délégation parallèle

Lancez ces agents **en parallèle** (un seul message, plusieurs appels) :

| Agent | Périmètre |
|-------|-----------|
| `seo-technique` | robots, sitemaps, canonicals, redirections, indexabilité, headers |
| `seo-performance` | LCP, INP, CLS mesurés via Chrome DevTools |
| `seo-contenu` | qualité, contenu mince, duplication, lisibilité |
| `seo-eeat` | Experience, Expertise, Autorité, Confiance |
| `seo-schema` | détection, validation, opportunités |
| `seo-crawler` | architecture, profondeur, orphelines |
| `seo-geo` | citabilité par les moteurs IA |
| `seo-data` | GSC + GA4 : ce qui performe réellement |

Chaque agent renvoie : un score /100, ses constats, et pour chaque constat
un correctif concret. Pas de « pensez à améliorer vos titres ».

## Phase 3 — Score de santé

| Catégorie | Poids | Justification du poids |
|-----------|-------|------------------------|
| Technique | 20 % | Un site non crawlable annule tout le reste |
| Contenu | 20 % | Ce qui fait réellement ranker en 2026 |
| On-page | 15 % | Le plus rapide à corriger |
| Maillage | 10 % | Sous-estimé, énorme effet de levier |
| E-E-A-T | 10 % | Décisif sur YMYL et sur la citation IA |
| Performance | 10 % | Départage à qualité égale |
| Schema | 5 % | Rich results, compréhension par les machines |
| GEO / IA | 10 % | Part de trafic croissante, encore peu disputée |

Le score global est une moyenne pondérée. **Affichez toujours le détail par
catégorie** : un 72/100 qui cache un 30/100 en technique n'est pas un 72.

Barème : 85-100 excellent · 70-84 bon · 50-69 à travailler ·
30-49 problèmes structurels · <30 refonte à envisager.

## Phase 4 — Priorisation (la partie qui compte)

Classez chaque constat sur deux axes : **impact trafic/CA estimé** et
**effort de mise en œuvre**. Puis quatre paquets :

1. 🔴 **Critique** — bloque l'indexation ou fait perdre du trafic maintenant.
   *Ex. : noindex sur une page à 4 000 impressions/mois, 404 sur une page qui recevait 12 backlinks.*
2. 🟠 **Fort impact, faible effort** — à faire cette semaine.
   *Ex. : title à réécrire sur 8 pages en position 9-14.*
3. 🟡 **Fort impact, effort élevé** — à planifier sur le trimestre.
   *Ex. : refonte de l'architecture des catégories.*
4. ⚪ **Faible impact** — à faire si on a le temps. Dites-le franchement.

**Maximum 5 items en 🔴.** Si vous en avez trouvé 12, c'est que 7 ne sont
pas critiques. Une liste de 40 problèmes non hiérarchisés ne sera jamais
traitée — c'est le mode d'échec le plus fréquent de l'audit SEO.

## Phase 5 — Livrables

Dans `seo-output/AAAA-MM-JJ-audit-<domaine>/` :

- `RAPPORT.md` — l'audit complet
- `PLAN-ACTION.md` — les corrections, par ordre d'exécution, avec pour
  chacune : le fichier ou l'URL concernée, le correctif exact, l'impact
  estimé, le temps de mise en œuvre
- `DONNEES.json` — tous les faits bruts, réutilisables par les autres skills
- `crawl.csv` — l'inventaire complet
- `screenshots/` — desktop + mobile si Chrome DevTools est branché

## Enchaînement

Un audit qui ne débouche sur rien ne sert à rien. Terminez en proposant, et
en lançant si l'utilisateur acquiesce :

- `/seo fix` — applique automatiquement les correctifs techniques sûrs
- `/seo quickwins` — attaque les positions 8-20
- `/seo maillage` — corrige les orphelines détectées
- `/seo geo` — si le score IA est faible

## Règles non négociables

- Jamais de chiffre inventé. Si la donnée manque : « donnée indisponible —
  nécessite [outil] », et on continue.
- Chaque constat s'accompagne du correctif exact, jamais d'un conseil vague.
- Toujours quantifier : « 23 pages concernées, 3 400 impressions/mois en jeu »,
  pas « plusieurs pages sont affectées ».
- Si un outil manque, dire ce que l'audit ne couvre pas plutôt que de
  faire semblant de l'avoir couvert.
