# Les SOP

Une SOP dit **quoi faire et dans quel ordre** ; le skill qu'elle cite le **fait**.
C'est ce qui rend le travail reproductible d'un site à l'autre.

Ce dossier est la **source unique** : une SOP qui change, change pour tous les
projets (elle est embarquée à chaque `projet.py sync` dans
`.claude/decupler-seo/docs/sop/`) et pour le playbook public
(https://decupler.com/claude-code-seo-os/), qui en reprend le contenu.

Chaque fiche suit le même format : objectif, quand, la phrase à dire à Claude,
la commande, les étapes, les MCP nécessaires, le livrable, les pièges.

| SOP | Skills | Commande |
|---|---|---|
| [Topical map](01-topical-map.md) | `seo-cartographie`, `seo-cocon-semantique` | `/seo cartographie, puis /seo cocon` |
| [Ligne éditoriale](02-ligne-editoriale.md) | `seo-opportunites`, `seo-keyword-research` | `/seo opportunites` |
| [Brief SEO/GEO](03-brief-seo-geo.md) | `seo-brief`, `seo-benchmark`, `seo-serp-analysis` | `/seo brief "<mot-clé>"` |
| [Rédaction](04-redaction.md) | `seo-redaction`, `seo-eeat` | `/seo article` |
| [Optimisation on-page](05-optimisation-on-page.md) | `seo-optimisation-onpage`, `seo-meta-serp`, `seo-quick-wins` | `/seo onpage <url> <mot-clé>` |
| [Maillage interne](06-maillage-interne.md) | `seo-maillage-interne` | `/seo maillage` |
| [Entités](07-entites.md) | `seo-entites-triplets`, `geo-llms-txt` | `/seo entités` |
| [Données structurées](08-donnees-structurees.md) | `seo-schema-jsonld` | `/seo schema` |
| [Design de page](09-design-de-page.md) | `seo-design-pages`, `seo-page-builder-html` | `/seo design, puis /seo page` |
| [Intégration CMS](10-integration-cms.md) | `seo-publication-cms` | `/seo publish` |
| [Indexation](11-indexation.md) | `seo-indexation` | `/seo index` |
| [Analyse GSC / GA4](12-analyse-gsc-ga4.md) | `seo-gsc-analyses`, `seo-quick-wins` | `/seo quickwins, ou /seo gsc` |
| [Visibilité IA](13-visibilite-ia.md) | `geo-share-of-model`, `geo-visibilite-ia`, `geo-citation-tracker` | `/seo geo <url>, ou /seo share-of-model` |
| [Reporting](14-reporting.md) | `seo-reporting`, `seo-dashboard`, `seo-pilotage` | `/seo rapport, puis /seo dashboard` |
| [La semaine type](15-semaine-type.md) | `seo-cycle`, `seo-pilotage`, `seo-journal-mesure` | routine `hebdo`, puis `/seo-maj` le lundi |
| [Arbitrer les actions](16-arbitrer-les-actions.md) | `seo-opportunites`, `seo-pilotage` | `/seo opportunites` |
| [Travailler avec un prestataire](17-travailler-avec-un-prestataire.md) | tous, selon la tâche | `/seo doctor`, puis la SOP de la tâche |

Dans Claude Code : « suis la SOP brief pour "<mot-clé>" » suffit, Claude lit la
fiche et lance le skill.
