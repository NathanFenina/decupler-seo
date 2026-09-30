# Claude Code SEO Décupler

**Le SEO et le GEO de Décupler, en plugin Claude Code.**
Une méthode qui audite, corrige, rédige, publie — puis **mesure si ça a marché**, et apprend de chaque site.

[![Contrôles](https://github.com/NathanFenina/decupler-seo/actions/workflows/ci.yml/badge.svg)](https://github.com/NathanFenina/decupler-seo/actions/workflows/ci.yml)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-D97757)](https://code.claude.com)
[![Licence MIT](https://img.shields.io/badge/licence-MIT-yellow)](LICENSE)
[![Français](https://img.shields.io/badge/langue-fran%C3%A7ais-blue)](#)

49 skills · 15 agents · 29 scripts Python (le cœur sans aucune dépendance) · 13 MCP préconfigurés · 297 tests

---

## Deux façons de l'utiliser

| | **Travailler avec Claude** | **Piloter des sites en autonomie** |
|---|---|---|
| Pour | un audit, une page à optimiser, un brief, un article — en direct | laisser des routines faire le travail chaque semaine |
| Installation | le plugin, en deux commandes | un dépôt privé par site, créé en une commande |
| Ce que ça garde | rien : chaque session repart de zéro | la mémoire du site, ses décisions, ce qui a marché |
| Qui | vous, votre équipe, vos clients | une agence, un consultant, un site avec de l'ambition |

Les deux utilisent la même méthode. Commencez par le plugin ; passez aux
projets quand vous voulez que ça tourne sans vous.

---

## Travailler avec Claude — 2 minutes

```
/plugin marketplace add NathanFenina/decupler-seo
/plugin install decupler-seo@decupler
```

Puis, dans n'importe quel projet :

```
/seo doctor
```

Il vous dit ce qui est branché, ce qui manque, combien ça coûte, et lance la
première action utile. Vous n'avez rien d'autre à lire pour démarrer.

Ensuite, parlez normalement :

> *« Audite exemple.com »* · *« Pourquoi cette page ne ranke pas ? »* ·
> *« Quelles pages rattraper ce mois-ci ? »* · *« Écris un article sur X »* ·
> *« Pourquoi ChatGPT ne me cite pas ? »* · *« J'ai perdu du trafic »*

Ou les commandes :

| | |
|---|---|
| `/seo audit <url>` | audit complet, 8 spécialistes en parallèle, score /100, plan priorisé |
| `/seo quickwins` | les pages en position 4-20 à rattraper, chiffrées, corrections écrites |
| `/seo onpage <url> <mot-clé>` | note /100 critère par critère, **puis réécrit** la page |
| `/seo fix <url>` | détecte **et corrige** la technique : robots, canonicals, redirections |
| `/seo brief <mot-clé>` | brief adossé à la SERP réelle, réponse directe et FAQ déjà rédigées |
| `/seo article` | rédaction : recherche obligatoire, thèse, zéro chiffre inventé |
| `/seo geo <url>` | visibilité dans ChatGPT, Gemini, AI Overviews, et comment y entrer |
| `/seo rapport` | le mois écoulé : ce qui a bougé, **pourquoi**, et quoi faire |

---

## Piloter des sites en autonomie

Une routine Claude Code tourne dans le cloud, même ordinateur éteint — mais
elle ne charge pas les plugins. Elle ne voit que ce qui est dans le dépôt
qu'elle clone. Chaque site a donc **son dépôt privé**, avec la méthode
embarquée et sa propre mémoire :

```bash
# un nouveau site
python3 scripts/projet.py init ../mon-site --nom "Mon site" --domaine https://mon-site.com

# un dépôt qui existe déjà — rien n'est écrasé sans le dire
python3 scripts/projet.py adopter ../site-existant --nom "Site" --domaine https://site.com

# mettre à jour la méthode d'un projet
python3 .claude/decupler-seo/scripts/projet.py sync .
```

Ou dites simplement à Claude : *« nouveau projet »*.

```
mon-site/                       dépôt PRIVÉ
├── CLAUDE.md                   la mémoire, chargée à chaque session et chaque routine
├── decupler-seo.config.yml     mode, plafonds, règles propres au client
├── memoire/
│   ├── marque.md               voix, lexique, interdits
│   ├── faits.md                la seule source des chiffres du site
│   ├── decisions.md            ce qui a été validé ou refusé — ne revient pas
│   └── apprentissages.md       ce qui marche sur CE site, mesuré
├── journal/modifications.csv   chaque modification, et son effet à J+28
├── ROUTINES.md                 les 4 routines, prêtes à créer
└── .claude/                    la méthode, synchronisée depuis ce dépôt
```

### Quatre routines

| | Quand | Publie seule | Vous soumet |
|---|---|---|---|
| **Veille** | chaque jour | rien — contrôle chaque URL du sitemap | les anomalies |
| **Optimisation** | lundi | titles, metas, FAQ, schema, liens internes | les réécritures de sections |
| **Contenu** | mercredi | rien | les pages neuves (brouillon ou pull request) |
| **Rapport** | le 1er | le rapport | les retours arrière proposés |

Votre temps : **30 minutes le lundi**, à lire `rapports/a-valider.md`.

### De l'idée au rapport, avec des chiffres à chaque étape

| Étape | Outil | Ce qui en sort |
|---|---|---|
| Idées | `demande.py idees --lexique` (DataForSEO, sans connecteur) | la demande réelle : volume, difficulté, intention, tendance |
| Priorités | `opportunites.py --calendrier` | actions classées par valeur pour **ce** client, funnel, calendrier éditorial |
| Brief | `serp_concurrents.py` + `seo-benchmark` + `seo-brief` | top 5 lu et mesuré (longueur cible, sujets récurrents, questions non traitées, AI Overview), puis brief en 14 sections : failles des concurrents, plan, H1 et intro rédigés |
| Rédaction | `style_maison.py` + `seo-redaction` + `controle_contenu.py` | texte écrit dans le style mesuré du client, relu, contrôlé, bloqué s'il contient une promesse ou un chiffre non sourcé |
| Publication | `wp.py` (WordPress) | brouillon par défaut, révision à valider pour une page en ligne, meta relue puis journalisée, carte de contenu et maillage |
| Mesure | `journal.py` | chaque modification jugée à J+28 contre un témoin |
| Rapport | `rapport.py` | les chiffres du mois calculés par script ; l'agent rédige seulement les causes |
| Visibilité IA | `share_of_model.py` | part de voix dans ChatGPT et Gemini, prompts où vous manquez |

### Ce qui le distingue : la boucle de mesure

Automatiser une modification est facile. Savoir si elle a aidé, presque
personne ne le fait.

Chaque modification publiée est inscrite avec ses chiffres Search Console
des 28 jours précédents, puis **remesurée à J+28** contre un **groupe
témoin** — les pages du site qui n'ont pas bougé. Si tout le site a pris
+12 % sur la période, une page à +17 % n'a gagné que 5 points grâce à la
modification : verdict « neutre », pas « gain ».

Les pertes sont proposées au retour arrière. Au bout de trois mesures du
même type, un apprentissage entre dans la mémoire du site — et le cycle en
tient compte : ce qui nuit **sur ce site-là** cesse d'être appliqué
automatiquement.

```bash
python3 scripts/journal.py mesurer-tout --auto     # chiffres et témoin relevés dans Search Console
python3 scripts/journal.py bilan                   # ce qui marche ici, et ce qui ne marche pas
```

Détail complet : [docs/PROJETS.md](docs/PROJETS.md)

---

## Les garde-fous

Le mode autonome écrit sur des sites en production. Voilà ce qui l'empêche
de mal faire.

**Un kill-switch à trois niveaux** : `SEO_SAFE_MODE=1` (dans le shell ou le
`.env` du projet), le flag `--safe`, ou `mode: safe` dans la config. Ou
dites à Claude : *« passe en safe mode »*.

**Ce qu'il ne fait jamais seul, quel que soit le mode :**
- supprimer un contenu
- poster sur un forum ou envoyer un email — le compte en jeu est le vôtre
- écrire sur un domaine que vous n'avez pas déclaré
- générer plus de 500 pages sans audit qualité d'un échantillon
- toucher robots.txt, les redirections ou les canonicals sans montrer le diff

**Ce qu'il fait toujours :** sauvegarder avant d'écrire, journaliser, passer
un contrôle qualité bloquant (`controle_contenu.py`) avant de publier,
laisser une trace de chaque exécution.

**Ce qu'il n'invente jamais :** un chiffre. Une donnée absente s'écrit
« nécessite tel outil ».

Nouveau projet = mode `assisted` : tout est préparé, rien ne part sans vous.
Passez en `autonomous` quand les premières mesures sont bonnes.
→ [docs/SECURITE.md](docs/SECURITE.md)

---

## Les outils

**Aucun n'est obligatoire.** Les skills s'adaptent à ce qui est branché et
disent ce qui manque.

| | Outils | Coût |
|---|---|---|
| **Le socle** | Search Console · GA4 · Chrome DevTools | gratuit |
| **La donnée marché** | Firecrawl · DataForSEO · Ubersuggest | gratuit à quelques € |
| **La production** | WordPress · Webflow · Notion · Semrush · Ahrefs | variable |
| **La visibilité IA** | clés OpenAI et Gemini (Claude et Perplexity en option) · Reddit | quelques centimes par mesure |

Search Console, GA4 et Chrome DevTools couvrent l'essentiel, et sont gratuits.
Search Console se lit aussi en direct, sans intermédiaire, avec
`scripts/gsc.py` et une clé de compte de service.
→ [docs/MCP.md](docs/MCP.md)

---

## La méthode

<details>
<summary><b>49 skills</b>, en 8 familles</summary>

| Famille | Skills |
|---|---|
| **Diagnostic et technique** | `seo-onboarding` · `seo-audit-360` · `seo-technique-autofix` · `seo-crawl-architecture` · `seo-core-web-vitals` · `seo-indexation` · `seo-migration` · `seo-veille` |
| **Données Search Console** | `seo-gsc-analyses` — 21 analyses : content decay, gagnants et perdants, requêtes émergentes, saisonnalité, cannibalisation, pages à créer… |
| **Recherche et stratégie** | `seo-opportunites` · `seo-cartographie` · `seo-quick-wins` · `seo-keyword-research` · `seo-competitor-gap` · `seo-benchmark` · `seo-cocon-semantique` · `seo-serp-analysis` · `seo-traffic-drop` |
| **Contenu** | `seo-brief` · `seo-redaction` · `seo-optimisation-onpage` · `seo-meta-serp` · `seo-faq-paa` · `seo-eeat` · `seo-comparatifs` |
| **Structure et échelle** | `seo-design-pages` · `seo-page-builder-html` · `seo-programmatique` · `seo-maillage-interne` · `seo-schema-jsonld` · `seo-entites-triplets` · `seo-hreflang-i18n` · `seo-images` |
| **GEO — moteurs IA** | `geo-visibilite-ia` · `geo-citation-tracker` · `geo-llms-txt` · `geo-share-of-model` |
| **Autorité** | `seo-netlinking` · `seo-reddit-communautes` · `seo-local` · `seo-digital-pr` |
| **Pilotage** | `seo-nouveau-projet` · `seo-cycle` · `seo-journal-mesure` · `seo-publication-cms` · `seo-pilotage-notion` · `seo-reporting` · `seo-dashboard` · `seo-ecommerce` |

→ [docs/SKILLS.md](docs/SKILLS.md)
</details>

<details>
<summary><b>15 agents</b> spécialistes, exécutés en parallèle</summary>

`seo-manager` (pilote un projet) · `seo-technique` · `seo-performance` ·
`seo-contenu` · `seo-redacteur` · `seo-data` · `seo-serp` · `seo-schema` ·
`seo-geo` · `seo-netlinking` · `seo-frontend` · `seo-crawler` ·
`seo-strategiste` · `seo-publisher` · `seo-analyste-concurrence`

→ [docs/AGENTS.md](docs/AGENTS.md)
</details>

<details>
<summary><b>Les principes</b> que tous suivent</summary>

1. **Jamais de chiffre inventé.** Donnée absente = « nécessite tel outil ».
2. **Toujours quantifier.** « 23 pages, 3 400 impressions en jeu », jamais « plusieurs pages ».
3. **Chaque constat a son correctif écrit**, prêt à appliquer.
4. **Cinq urgences au plus.** Une liste de 40 problèmes n'est jamais traitée.
5. **Une page ne sort que si elle bat la meilleure concurrente** sur au moins 5 axes.
6. **Vérifier qu'il faut écrire** avant d'écrire : deux pages sur la même intention se neutralisent.
7. **Ne jamais bloquer sur un outil manquant** : dire ce qui n'est pas couvert, et continuer.
</details>

---

## Prérequis

Claude Code · Node (pour les MCP) · Python 3.10+ · Chrome, optionnel.

Les scripts n'ont **aucune dépendance** — y compris la connexion à Search
Console. Seuls le crawler et l'analyse de pages utilisent `requests` et
`beautifulsoup4` : `pip install -r requirements.txt`.

---

## Documentation

| | |
|---|---|
| [Installation](docs/INSTALLATION.md) | les trois façons d'installer |
| [Piloter des projets](docs/PROJETS.md) | mémoire, routines, boucle de mesure |
| [Brancher les outils](docs/MCP.md) | Search Console, GA4, et les 11 autres |
| [Les skills](docs/SKILLS.md) · [Les agents](docs/AGENTS.md) | ce que fait chacun |
| [Les workflows](docs/WORKFLOWS.md) | les chaînes de bout en bout |
| [Sécurité](docs/SECURITE.md) · [Dépannage](docs/DEPANNAGE.md) | |
| [Contribuer](CONTRIBUTING.md) | |

---

## Ce que ça ne fait pas

- **Ça ne remplace pas un stratège.** Ça exécute vite et bien, ça priorise
  correctement ; les arbitrages business restent les vôtres.
- **Ça ne garantit aucun classement.** Personne ne le peut. Ça fait le travail
  correctement — et ça mesure honnêtement s'il a porté.
- **Ça ne crée pas d'autorité à votre place.** Les liens et les mentions
  s'obtiennent auprès de vraies personnes. Le dispositif prépare tout, vous
  envoyez.
- **Ça ne triche pas.** Pas de contenu mince à la chaîne, pas de spam de
  forums, pas de faux avis, pas de preuve inventée.

---

<div align="center">

MIT · Construit par **[Décupler](https://decupler.com)**, agence SEO & GEO

</div>
