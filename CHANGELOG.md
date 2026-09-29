# Journal des versions

## 3.0.0 — decupler-seo

Nouveau dépôt, nouveau nom de plugin : `decupler-seo`. L'installation se
fait par `/plugin install decupler-seo@decupler`.

### Ajouté — le pilotage autonome de projets

- **Gabarit de projet** (`modele-projet/`) : un dépôt privé par site, avec sa
  mémoire (`CLAUDE.md`, `memoire/marque.md`, `decisions.md`,
  `apprentissages.md`), sa configuration, son journal et ses routines.
- **`scripts/projet.py`** : `init` crée un projet, `sync` y embarque la
  méthode, `statut` vérifie sa version et son intégrité. La synchronisation
  refuse d'écraser un fichier de méthode modifié à la main dans un projet.
  Les routines ne chargeant pas les plugins, c'est ce qui leur donne accès
  à la méthode.
- **Boucle de mesure** (`scripts/journal.py`, skill `seo-journal-mesure`) :
  chaque modification est journalisée avec sa situation de départ, remesurée
  à J+28 contre un groupe témoin, jugée, et les pertes sont proposées au
  retour arrière. Les apprentissages ne sont tirés qu'à partir de trois
  mesures du même type.
- **Skill `seo-cycle`** : les quatre modes des routines — veille,
  optimisation, contenu, rapport — avec niveaux d'autonomie, plafonds et
  journal de chaque exécution.
- **Skill `seo-nouveau-projet`** et **agent `seo-manager`**.
- `docs/PROJETS.md`.


## 2.0.0 — Claude Code SEO Décupler

Refonte complète. Le dépôt devient un dispositif SEO + GEO agentique et
francophone, packagé en plugin Claude Code.

### Ajouté

**40 skills**, organisés en 7 blocs : diagnostic et technique · recherche et
stratégie · contenu · structure et échelle · GEO · autorité et acquisition ·
production et pilotage.

**14 agents spécialisés**, exécutables en parallèle : technique, performance,
contenu, rédacteur, data, SERP, schema, GEO, netlinking, frontend, crawler,
stratège, publisher, analyste concurrence.

**13 MCP préconfigurés** dans `.mcp.json` : DataForSEO, Ahrefs, Semrush,
Ubersuggest, Search Console, GA4, Firecrawl, Chrome DevTools, WordPress,
Webflow, Notion, Perplexity, Reddit. Tous optionnels, avec repli gracieux.

**15 commandes** dont un routeur `/seo` qui comprend le langage naturel.

**Mode autonome avec kill-switch à trois niveaux** — variable
d'environnement, flag de commande, configuration — et sept garde-fous durs
non désactivables.

**13 scripts d'analyse** : récupération de page, crawler, PageRank interne, scoring on-page /100,
validation de schema, analyse de redirections, validation hreflang, audit
d'images, analyse d'export Search Console, share of model, restauration CMS,
garde-fou et diagnostic.

**Pilotage Notion** : cinq bases — Leads & Prospects, Objectifs & KPI,
Roadmap SEO, Briefs & Contenus, Backlinks — alimentées automatiquement par
les skills.

**Cinq chaînes agentiques** câblées bout en bout : quick wins, brief,
article, score de visibilité IA, rapport mensuel.

### Modifié

- Tout le dépôt passe en français.
- Les 12 skills anglais de la version 1 sont remplacés.
- Publication en brouillon par défaut, même en mode autonome.

### Notes techniques

- INP est la seule métrique d'interactivité. FID n'est mentionné nulle part.
- Les dépréciations Google sont signalées : rich result HowTo (sept. 2023),
  FAQ restreint (août 2023), SpecialAnnouncement (juillet 2025).
- Seuils anti-contenu mince : alerte à 100 pages programmatiques, blocage à
  500 ; alerte à 30 pages locales, blocage à 50.
