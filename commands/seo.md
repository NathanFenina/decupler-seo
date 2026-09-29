---
description: Routeur principal Claude Code SEO Décupler — dirige vers le bon skill selon ce que vous demandez
argument-hint: "[audit|opportunites|cartographie|quickwins|gsc|brief|benchmark|article|onpage|page|fix|geo|backlink|publish|rapport|notion|cycle|doctor] <url ou sujet>"
---

# /seo — routeur

Argument reçu : `$ARGUMENTS`

## Si aucun argument

Lancez `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py"`, puis proposez en trois lignes ce qui est
possible avec les outils branchés, et exécutez l'action la plus utile. Ne
laissez jamais l'utilisateur devant un menu.

## Routage

| Ce qui est demandé | Skill |
|--------------------|-------|
| `audit`, une URL de domaine seule | `seo-audit-360` |
| `opportunites`, `priorités`, `par où commencer` | `seo-opportunites` |
| `cartographie`, `mot-clé principal`, `prompt principal` | `seo-cartographie` |
| `quickwins`, `gains rapides` | `seo-quick-wins` |
| `technique`, `fix`, `corrige` | `seo-technique-autofix` |
| `crawl`, `architecture` | `seo-crawl-architecture` |
| `perf`, `cwv`, `vitesse` | `seo-core-web-vitals` |
| `index`, `indexation` | `seo-indexation` |
| `migration`, `refonte` | `seo-migration` |
| `motscles`, `keywords` | `seo-keyword-research` |
| `concurrent`, `gap` | `seo-competitor-gap` |
| `cocon`, `silo` | `seo-cocon-semantique` |
| `serp` | `seo-serp-analysis` |
| `chute`, `baisse` | `seo-traffic-drop` |
| `brief` | `seo-brief` |
| `article`, `rédige` | `seo-redaction` |
| `onpage`, `score`, `optimise` | `seo-optimisation-onpage` |
| `meta`, `title` | `seo-meta-serp` |
| `faq` | `seo-faq-paa` |
| `eeat` | `seo-eeat` |
| `page`, `html` | `seo-page-builder-html` |
| `design`, `maquette`, `gabarit`, `cta`, `bannière` | `seo-design-pages` |
| `programmatique` | `seo-programmatique` |
| `maillage`, `liens internes` | `seo-maillage-interne` |
| `schema`, `jsonld` | `seo-schema-jsonld` |
| `hreflang`, `international` | `seo-hreflang-i18n` |
| `images` | `seo-images` |
| `geo`, `ia`, `chatgpt` | `geo-visibilite-ia` |
| `citation` | `geo-citation-tracker` |
| `llmstxt`, `entité` | `geo-llms-txt` |
| `triplets`, `entités`, `knowledge graph`, `cohérence des faits` | `seo-entites-triplets` |
| `share-of-model`, `part de voix` | `geo-share-of-model` |
| `backlink`, `netlinking` | `seo-netlinking` |
| `reddit`, `communautés` | `seo-reddit-communautes` |
| `local`, `gbp` | `seo-local` |
| `pr`, `étude`, `linkbait` | `seo-digital-pr` |
| `publish`, `publie` | `seo-publication-cms` |
| `notion`, `pilotage` | `seo-pilotage-notion` |
| `rapport`, `reporting` | `seo-reporting` |
| `dashboard` | `seo-dashboard` |
| `comparatif`, `vs` | `seo-comparatifs` |
| `ecommerce`, `boutique` | `seo-ecommerce` |
| `veille`, `monitoring` | `seo-veille` |
| `doctor`, `install`, `configure` | `seo-onboarding` |
| `nouveau-projet`, `nouveau client` | `seo-nouveau-projet` |
| `cycle`, `veille quotidienne`, `routine` | `seo-cycle` (préciser le mode) |
| `journal`, `mesure`, `est-ce que ça a marché` | `seo-journal-mesure` |
| `gsc`, `search console`, `cannibalisation`, `ctr` | `seo-gsc-analyses` |
| `benchmark`, `faire mieux que` | `seo-benchmark` |

Si la demande ne correspond à rien de précis, lancez `seo-audit-360` : c'est
le point d'entrée qui produit le plus de valeur sans contexte.

## Options globales

- `--safe` : force le mode sûr pour cet appel, aucune écriture externe
- `--verbose` : détaille les appels d'outils
