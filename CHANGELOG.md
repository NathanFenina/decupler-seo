# Journal des versions

## 3.1.0

### Ajouté

- **Mesure branchée sur Search Console, sans dépendance** : `scripts/gsc.py`
  (performances, page, instantané hebdomadaire, groupe témoin, sitemaps,
  inspection d'URL). La clé de compte de service est signée en Python pur :
  rien à installer, y compris dans une routine cloud. `journal.py ajouter
  --auto` relève la situation de départ, `mesurer-tout --auto` juge toutes
  les modifications arrivées à échéance.
- **Skill `seo-gsc-analyses`** : 20 analyses Search Console prêtes à lancer,
  en trois familles — diagnostiquer, piloter, produire.
- **Skill `seo-benchmark`** : avant toute page, les trois meilleures pages
  concurrentes, dans chaque langue du projet ; la page ne sort que si elle
  les bat sur au moins cinq axes.
- **`scripts/controle_contenu.py`** : contrôle bloquant avant publication
  (textes provisoires, promesses invérifiables, interdits du client,
  longueurs de title et meta, H1, alt). Lit le HTML, le Markdown et le JSON
  des sites en code.
- **`scripts/seo_live.py`** : santé du site en production (robots.txt,
  sitemap, statut, noindex, canonical de chaque URL) et notification
  IndexNow.
- **`projet.py adopter`** : greffe la méthode sur le dépôt existant d'un
  site, sans rien écraser.
- **Deux modes de publication** : `cms` (API) et `depot` (branche, contrôles,
  pull request ; la fusion est la mise en ligne).
- `memoire/faits.md` dans le gabarit : les chiffres vérifiés du client, avec
  leur source, que les contenus peuvent citer.
- Tests (`tests/`, bibliothèque standard) et intégration continue : Python
  3.10 et 3.13, validation du plugin, création d'un projet de bout en bout.
- `SECURITY.md`.

### Modifié

- `seo-redaction` : passe anti-cannibalisation, thèse avant le plan, test
  anti-remplissage, singularité des pages issues d'un gabarit.
- `seo-netlinking` : ce que l'on offre en échange de chaque type de lien.
- `geo-share-of-model` : distingue la visibilité non marquée de la
  réputation de marque, trois formulations par sujet, tonalité.
- La configuration se lit avec sa structure : `publication.mode: depot` ne
  se confond plus avec le `mode` du projet.
- Le groupe témoin n'est utilisé qu'au-delà de 200 clics.

### Corrigé

- La synchronisation signale un fichier du projet qui porte le nom d'un
  fichier de méthode, au lieu de l'écraser.


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
