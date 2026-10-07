# Journal des versions

## 3.11.0

### Ajouté

- **Suivi mensuel des positions et des prompts** (`scripts/suivi.py`, skill
  `seo-suivi-mensuel`) : position réelle de chaque mot-clé principal de la
  cartographie dans Google (DataForSEO, sans attendre l'accès Search Console),
  page qui ranke, concurrent devant, AI Overview ; batterie de prompts
  proposée puis **validée par le client** (`recherche/prompts-suivi.csv`,
  statut propose / valide / refuse, on ajoute sans jamais retirer), relevée
  chaque mois sur les moteurs IA ; comparaison au mois précédent dans
  `rapports/suivi-AAAA-MM.md`. Branché dans la routine de rapport.

## 3.10.1

- **Indexation au déploiement**, comme l'indexation instantanée de Rank Math : le
  workflow `indexation.yml` se déclenche aussi sur `deployment_status` (déploiement
  réussi en production sur Vercel, Netlify…), en plus du passage quotidien. SOP 11 :
  site déployé à la main, `indexation.py annoncer` en fin de script de déploiement.

## 3.10.0

### Ajouté

- **Indexation automatique** : `indexation.py auto` lit le sitemap (robots.txt,
  index de sitemaps) et annonce les pages dont le `lastmod` est récent ;
  gabarit `.github/workflows/indexation.yml` (chaque jour, sans rien écrire
  dans le dépôt ; secrets `GSC_SA_JSON`, `GSC_SITE_URL`, `INDEXNOW_KEY`).
- **Le constat remonte au projet** : `indexation.py suivre` regroupe les URL
  non indexées par cause (404, explorée non indexée, détectée non indexée,
  inconnue, bloquée) avec une proposition par groupe dans
  `rapports/a-valider.md`. Le script ne décide rien.
- **`docs/PRISE-EN-MAIN.md`** : trois parcours cochables (plugin en 15 min,
  premier projet en 1 h, prestataire), avec ce qu'on doit voir à chaque étape
  et un tableau « quand ça bloque ». Lien en tête du README et du manuel.

### Modifié

- **La routine hebdo passe au mercredi** (gabarit, skills seo-cycle,
  seo-pilotage, seo-nouveau-projet, SOP 11, 14, 15, 16, manuel) ; rapport le
  premier mercredi du mois. `rapport.py` déduit le jour de la routine des
  passages trouvés (mercredi par défaut) au lieu de compter les vendredis.
- SOP 15 réordonnée autour du mercredi.
## 3.9.2

Retours de decupler.com (06/10/2026).

### Ajouté

- **`scripts/liens.py`** : profil de liens DataForSEO trié entre domaines
  propres et spam automatique (score de spam ≥ 30), spam compté par mois
  d'apparition (`resume`, `domaines --json`). Le chiffre utile est celui des
  domaines propres, pas le total.
- **`gsc.py inspect --json`** : une ligne JSON par URL (verdict, couverture,
  dernier passage, canonique Google et déclarée, sitemaps, liens vers) pour
  croiser l'indexation avec un crawl.

### Corrigé

- **Une routine ne fusionne jamais sa propre PR** (`hebdo`, `_commun`,
  `rapport`, `optimisation`, `seo-pilotage`) : la fusion sans relecture est
  refusée par la politique des sessions, et la question « fusionner ? » a
  bloqué la routine du 02/10/2026. La PR devient une action `bloquee` dans
  « À décider ».

## 3.9.1

Retours d'un projet en production : cinq skills propres au projet fusionnés
dans la méthode, cinq autres allégés au profit des skills de méthode. Une
seule version de chaque savoir-faire.

### Ajouté

- **`geo-linkedin`** : articles LinkedIn (page entreprise ou profil) qui
  servent la citation par les moteurs IA et l'entité sans dupliquer le site :
  trois formats (dérivé d'une page, réponse à un prompt, newsletter),
  anti-duplication contre la page source, fiche de publication manuelle
  (aucune API ne publie d'article long), mesure par les prompts à J+30.
- **`templates/wordpress/plugins/seo-indexnow/`** : clé IndexNow servie à la
  racine et envoi à chaque publication d'un contenu public (hors noindex,
  brouillons, médias), uniquement en production ; route d'état. Testée sur un
  WordPress local.
- **Manuel** : « Comment ça marche, en deux minutes » et six tutos pas à pas
  (mettre à jour, faire remonter une amélioration, plugin du poste, nouveau
  projet, confier une tâche, état de tous les projets). Lien en tête du README.
- **Gabarit** : `CLAUDE.md` dit à Claude comment mettre à jour la méthode et y
  remonter une amélioration ; la routine `hebdo` suit l'indexation
  (`indexation.py suivre`).
- **`scripts/netlinking_score.py`** : classe les cibles d'une campagne de
  netlinking sur 100 (pertinence 40, autorité 25 et trafic 15 en échelle
  logarithmique, accessibilité 20), écarte d'office les domaines sans donnée
  (autorité 1, aucun lien), signale les cibles sans preuve mesurée. JSON ou
  CSV. Tests : `tests/test_netlinking_score.py`.
- **`scripts/photos_libres.py`** : vraies photos de lieux sur Wikimedia
  Commons, licence libre, auteur et crédit prêts à afficher ; écarte
  gravures, plans, blasons et licences non libres ; vignette à la largeur
  utile (l'original fait répondre 429). Tests : `tests/test_photos_libres.py`.
- **`scripts/rendu.py`** : rendu Chromium sans interface et sonde de
  débordement dans le DOM (la capture ne fait pas foi), cache local
  d'images et de polices, page complète ou fragment. Pour les sessions et
  routines sans MCP Chrome DevTools. Tests : `tests/test_rendu.py`.
- **`seo-programmatique`** : section « Pages ville d'un prestataire de
  service » : calibrage sur la SERP mesurée (la longueur ne décide pas, la
  preuve si), jamais d'adresse ni de clientèle locale inventée,
  `areaServed` et cadrage honnête, registres agence / consultant, page
  comparatif pour l'intention mixte, maillage à cinq liens, données et
  blocs rédigés séparés, carte de zone en SVG. Renvoi depuis `seo-local`.
- **`seo-maillage-interne`** : « Poser un lien sans abîmer le texte » :
  ancre déjà présente, jamais en contexte négatif ni dans un Hn,
  dictionnaire d'ancres, dans un lot programmé un contenu ne lie que ses
  prédécesseurs de parution, URL en 410 exclues.
- **`seo-design-pages`** : signatures d'une interface générée et détecteur
  en mode navigateur, correction à la source (`design-tokens.md`, § 5 bis) ;
  rythme vertical (§ 5 ter) ; `ch` trompeur avec certaines polices,
  plancher de 12 px ; animations en translation déclenchées au défilement,
  animation de fond (canvas) ; registre des visuels, photos Commons
  créditées, logos ramenés à une teinte, pièges `aspect-ratio` et
  sélecteur après enveloppe wpautop (`images.md`) ; la matière qui
  différencie une page service (`gabarits-par-type-de-page.md`) ; `100vw`
  et barre de défilement, `sticky` natif (`integration-plateformes.md`).

### Modifié

- **`wp.py carte`** compte les mots d'une page Elementor depuis
  `_elementor_data` quand l'API l'expose : une page riche n'y apparaît plus
  « vide » (et `seo-audit-contenu` ne la condamne plus).
- **`seo-audit-contenu`** : pages construites avec un constructeur ; portée
  réelle des motifs d'obsolescence (zones affichées et termes principaux) ;
  pages d'une extension e-commerce abandonnée ; un seul gestionnaire de
  redirections ; refonte d'un lead magnet périmé. Correction de l'exemple
  YAML : une seule barre oblique inverse, guillemets simples (l'exemple
  doublé ne trouvait jamais rien).
- **`seo-entites-triplets`** : correction du graphe côté serveur, une fois
  pour tout le site ; vérification après correction (une `Organization`,
  une `Person`, plus d'empreinte de l'extension SEO, test des résultats
  enrichis).
- **`seo-netlinking`** : ligne de base sans Ahrefs ; ceux qui rankent déjà
  sur vos requêtes en première source ; données propriétaires préalables
  aux médias à forte autorité ; prescripteurs ; format du fichier de
  cibles ; interdits de campagne (échange réciproque, annuaire généraliste,
  envoi en masse) ; statuts de suivi.
- **`seo-redaction`** : butin minimum avant d'écrire et questions de la
  SERP ; plan profond et trame d'un article expert ; longueur minimale
  quand un plancher d'occurrences et un plafond de densité s'imposent
  ensemble ; exception de la page d'accueil.
- **`seo-keyword-research`** et **`seo-opportunites`** : recherche avec le
  MCP Ubersuggest (langue et pays à chaque appel, volumes mondiaux sans
  `locId`, pas d'AI Overview exposé) ; impressions comme borne basse d'un
  volume inconnu ; filtre des termes ambigus par mot de contexte et liste
  négative.
- **`seo-publication-cms`** (`references/wordpress.md`) : contrôle après
  chaque envoi (dont le `<br />` entre deux JSON-LD et les `<p>` vides
  visibles seulement au DOM) ; capacité `unfiltered_html` exacte (éditeurs
  compris sur un site simple, corrigé aussi dans `integration-plateformes.md`) ;
  templates Elementor non relisibles, bascule `_elementor_edit_mode`,
  refonte à la même URL ; création cherchée par slug.
- **`seo-lead-magnet`** : légende des preuves chiffrées, `<p>` vides au DOM,
  gabarit sans en-tête, entrée de menu.

## 3.9.0

### Ajouté

- **Passe d'humanisation** : skill `seo-humanisation` et `scripts/humanisation.py`.
  Score des tics d'écriture générée en français (8 familles, signaux ligne par
  ligne), comparatif `--avant/--apres` qui bloque tout chiffre apparu, `--seuil`
  pour les contrôles. Marqueurs dans `config/marqueurs-ia-fr.json`, exceptions
  du projet dans `memoire/marqueurs-ia.json`. Appelée en fin de `seo-redaction`
  et dans la SOP 4. Elle rend un texte meilleur et reconnaissable comme celui du
  client ; elle ne promet pas d'être « indétectable ».
- **Indexation après publication** : `scripts/indexation.py` (`cle`, `annoncer`,
  `suivre`) : IndexNow, sitemaps resoumis par l'API, registre
  `donnees/indexation.csv`, inspection à J+3 et liste des URL à demander à la
  main. Pas d'Indexing API Google hors offres d'emploi et vidéos en direct.
- **`templates/wordpress/`** : trois extensions génériques, testées sur un
  WordPress réel avec Yoast et Rank Math. `seo-meta-rest.php` (mu-plugin :
  title, meta, requête, canonique, noindex écrivables par l'API pour Yoast,
  Rank Math et SEOPress), `seo-crawl-fix` (410 du spam par liste et motifs,
  sitemap des URL supprimées, page d'erreur légère, pagination hors limites,
  pages hors index, redirections, robots.txt, cache Elementor), `seo-entite`
  (Organisation, Personne, sameAs, identifiant unique dans le JSON-LD). README :
  incident, installation, test, désinstallation, niveau d'autonomie. `wp.py`
  renvoie vers le mu-plugin quand un champ SEO n'est pas écrit.
- **Mise à jour depuis un projet** : commande `/seo-maj` ; `projet.py remonter`
  (renvoie vers decupler-seo, sur une branche, les fichiers de méthode
  améliorés dans un projet) ; `projet.py completer` (ajoute à un projet existant
  les nouveautés du gabarit, sans rien remplacer).
- **Obsidian** : chaque projet s'ouvre comme coffre (`.obsidian/` partagé,
  `Accueil.md`, liens Markdown relatifs) ; `notes/` sert de boîte d'entrée
  humaine (`#a-traiter`, `#fait-client`), lue par la routine du vendredi.
- **SOP 15 à 17** : la semaine type, arbitrer les actions du mois (contenu,
  technique, GEO sur une même échelle), travailler avec un prestataire.
- **`docs/MANUEL.md`** : trois chemins de prise en main (essayer, rejoindre un
  projet, piloter des projets) et la circulation du savoir entre decupler-seo
  et les projets.

### Modifié

- `docs/PROJETS.md` : anatomie complète d'un projet, qui écrit quoi, skill de
  méthode ou skill `projet-`, Obsidian.
- SOP 11 : `indexation.py annoncer` puis `suivre` ; Claude in Chrome réservé à
  quelques URL, jamais en routine.

## 3.8.0

### Ajouté

- **Les 14 SOP** dans `docs/sop/` : une procédure par action (topical map,
  ligne éditoriale, brief, rédaction, on-page, maillage, entités, données
  structurées, design, intégration CMS, indexation, analyse GSC/GA4,
  visibilité IA, reporting), chacune reliée au skill qui l'exécute. Source
  unique, embarquée dans chaque projet (`.claude/decupler-seo/docs/sop/`).
- **Synchro automatique des projets** : `modele-projet/.github/workflows/sync-methode.yml`,
  installé par `init` et `adopter`. Chaque lundi, il synchronise la méthode
  depuis GitHub et ouvre une pull request si elle a changé.
- **Registre des projets** : `projets.json` et `python3 scripts/projet.py registre`
  (version embarquée de chaque projet, synchro auto présente ou non, ce qui
  est à synchroniser).
- `seo-audit-contenu` et `scripts/audit_contenu.py` : passe chaque contenu du
  site au crible (vide, mort, daté, mince, à pousser, technique) en croisant
  la carte de contenu et la Search Console.
- `seo-lead-magnet` : une page qui donne tout, ranke, et capture l'email
  (pop-up obligatoire seulement pour le trafic de campagne, livrable verrouillé).
- `scripts/similarite_lot.py` : détecte les pages trop semblables dans un lot
  (phrases communes, part de contenu unique).
- Enrichis avec ce qui a été appris sur des projets réels : `seo-entites-triplets`
  (fiche d'identité, un `@id` par entité, doublons de Person), `seo-netlinking`
  (qualification, relances), `seo-optimisation-onpage`, `seo-programmatique`,
  `seo-pilotage-notion`, `seo-publication-cms` (pièges WordPress),
  `seo-design-pages` (checklist design, intégration).

### Brief SEO/GEO

- `seo-brief` passe à **18 sections** : réponse directe de 40-60 mots
  rédigée, matrice de gap face au top 5, volumes et longue traîne tracés
  par source, **prompts IA et fan-out** (section 13), données structurées
  recommandées (14), sources et E-E-A-T à apporter (15), checklist GEO
  avant publication (16), bloc de traçabilité des données.
- `serp_concurrents.py` fonctionne **sans DataForSEO** : `--serp-firecrawl`
  (recherche Firecrawl enregistrée, PAA et AI Overview notés « non
  mesurés »), `--pages-json` (pages déjà relevées, HTML ou Markdown),
  `--questions` (PAA relevées ailleurs), `--sitemap` (pages du client
  candidates au maillage interne).
- Lecture des pages : **entités nommées** (noms propres, outils, sigles)
  par page et communes au top, **vidéos** intégrées.

## 3.7.1

### Ajouté

- Page de suivi **aux couleurs du projet** : `pilotage.py injecter --theme`
  (mode sombre ou clair, couleurs, polices Google Fonts) ; en mode sombre la
  page suit la marque quel que soit le thème du lecteur.
- `seo-publication-cms` : pièges Elementor (rendu par `_elementor_data`,
  cache, gabarit canvas), double H1 des thèmes, filet `p:empty`, politique
  de mots de passe, comptes créés par un piratage.

## 3.7.0

### Ajouté

- **Rythme hebdo par défaut** : une seule routine par projet, le vendredi
  (`routines/hebdo.md`, mode `hebdo` de `seo-cycle`). Elle contrôle le site,
  mesure, exécute les actions validées et écrit le bilan de la semaine ; le
  premier vendredi du mois, elle fait aussi le rapport et les propositions.
  Les quatre routines séparées restent possibles pour les gros sites.
- **Page de suivi en onglets par mois** : « À décider » (bloqué, puis à
  valider rangé par chantier, avec remarque pour Claude), reporting, fait,
  à faire par chantier, wins, contenus avec lien Notion, semaine par semaine.
- `pilotage.py` : statut `bloquee` (`--attend` : qui ou quoi), chantiers
  (`--chantier`), historique daté (`ajouter --date`), `mois` (bilan de la
  semaine ou du mois, rejouable sans doublon), `sauvegarder` et `restaurer`
  (copie de la roadmap dans `journal/pilotage.json`, commitée).
- `rapport.py` compte les passages hebdo (un par vendredi) au lieu des veilles
  quand le projet tourne au rythme hebdo.

## 3.6.0

### Ajouté

- Gabarit `routines/` (règles communes + veille, optimisation, contenu,
  rapport) : les consignes des routines sont versionnées dans le dépôt du
  projet, et le prompt de chaque routine se contente de les lire.
- `docs/PROJETS.md` : pièges constatés en production et « Travailler projet
  par projet » (un dépôt, une conversation, une page de suivi par projet).

### Corrigé

- `demande.py idees` : quand la base DataForSEO Labs n'a pas la langue
  demandée pour le pays du projet (anglais en France), la demande est lue
  sur le marché naturel de la langue (États-Unis pour l'anglais) au lieu
  d'échouer ; `--pays` reste prioritaire.

## 3.5.3

### Corrigé

- Les fichiers de travail du tableau de bord (`donnees/pilotage.json`,
  `donnees/actions-*.json`) sont ignorés par git : ils laissaient l'arbre
  « sale » à la fin de la routine de rapport.
- Une routine dont la fusion de PR est refusée par les permissions ne reste
  plus en attente : PR laissée ouverte, signalée dans le journal de run et sur
  la page de suivi (`seo-pilotage`, `seo-cycle`).

## 3.5.2

### Ajouté

- `pilotage.py integrer` : loge le tableau de bord dans une page de suivi qui
  existe déjà, contenu d'origine conservé ; styles isolés (préfixe `pl-`) pour
  cohabiter avec la charte de la page hôte.

## 3.5.1

### Modifié

- Une page de suivi par projet (titre propre, onglets masqués pour un seul
  projet, section « Livrables et comptes rendus ») ; `pilotage.py ajouter`
  consigne une action faite ou décidée dans n'importe quelle conversation ;
  règle anti-doublon dans `seo-pilotage`.

## 3.5.0

### Ajouté

- **Tableau de bord partagé et roadmap validée** : `scripts/pilotage.py`,
  `templates/pilotage.html` et le skill `seo-pilotage`. Une page (Artifact) pour
  tous les projets : chiffres Search Console, cartographie, et chaque mois les
  actions proposées (au plus 8, dont 3 décisions) que le client valide d'un clic.
  Les routines n'exécutent que ce qui est validé et notent le résultat.
- `rapport.py` compte les routines aussi par leurs branches.

### Modifié

- Cartographie : cannibalisation par langue ; adresses hors sitemap écartées.

## 3.4.0

### Ajouté

- **La SERP lue page par page** : `scripts/serp_concurrents.py`. Une SERP
  DataForSEO (PAA dépliées, AI Overview et ses sources, features), puis le
  top 5 lu sans dépendance : plan H1-H3, listes, tableaux, mots, FAQ,
  schémas, dates, ton. En sortie, la fourchette de longueur mesurée
  (médiane → 3e quartile), les sujets de H2 récurrents, les questions
  qu'aucun titre du top ne traite, le champ sémantique commun et, avec
  `--url`, ce qui manque à la page du client. Repli payant optionnel par
  DataForSEO pour les pages bloquées.
- **Le style du client, mesuré** : `scripts/style_maison.py` écrit
  `memoire/style.md` (adresse, personne, rythme des phrases et des
  paragraphes, lisibilité, listes, ouvertures, expressions et vocabulaire
  récurrents) ; la section « Lecture », remplie à la main, est conservée
  d'une mesure à l'autre.
- `seo-brief` construit le plan à partir des sujets récurrents et des
  gaps mesurés ; `seo-redaction` écrit dans le style mesuré et le vérifie ;
  `seo-images` couvre l'illustration d'un contenu neuf.
- **Design des pages** : skill `seo-design-pages` (gabarit par type de
  page — service, article, page locale, landing, comparatif, outil, aimant à
  leads —, placement des CTA, bannières, plan d'images, tokens, pièges
  WordPress, checklist avant publication) et 11 nouveaux composants HTML
  (hero, CTA, témoignages, aimant à leads, sommaire, chiffres clés,
  comparatif, auteur, en bref, encadrés, figure légendée).
- **Images** : `scripts/images_generer.py` (Gemini, OpenAI en repli, prompt
  tiré du style du site, jamais de texte ni de logo, alt proposé) ;
  `audit_images.py` sans dépendance (alt, dimensions, image principale en
  lazy, poids, formats, doublons).
- **Publication WordPress** : `scripts/wp.py` (vérifier, publier en
  brouillon, média, title et meta journalisés, carte des contenus,
  maillage appliqué en révision, remplacement en masse), gardé par
  `guard.py`, sauvegarde avant chaque écriture.
- **Cartographie par site** : `scripts/cartographie.py` et le skill
  `seo-cartographie`. Une ligne par page avec son mot-clé principal et son
  prompt principal ; chaque mois, la position de la page sur son mot-clé et
  la citation du prompt par ChatGPT, Gemini et Claude ; historique, section
  du rapport mensuel, export Notion.
- **Triplets et entités** : `scripts/triplets.py` et le skill
  `seo-entites-triplets`. Les faits d'une page en triplets sujet —
  prédicat — objet, vérifiés contre le registre du projet
  (`memoire/triplets.csv`, `memoire/entites.csv`), contradictions entre
  pages, fragment JSON-LD `about`/`mentions` et recherche d'identifiant
  Wikidata.
- Le mode contenu de `seo-cycle` enchaîne SERP lue, brief avec triplets,
  rédaction dans le style mesuré, design, et cinq contrôles bloquants ;
  chaque page publiée entre au journal avec les requêtes qu'elle vise.


## 3.3.0

### Ajouté

- **Idées de contenu chiffrées** : `scripts/demande.py` (volumes, idées à
  partir de graines ou du lexique du projet, SERP d'un mot-clé avec PAA,
  AI Overview et recherches associées). DataForSEO en direct, coût affiché
  à chaque appel.
- **Calendrier éditorial** : `opportunites.py --calendrier` répartit les
  sujets par semaine (80 % création, 20 % optimisation, mix
  TOFU/MOFU/BOFU réglable par projet, une seule optimisation par page),
  avec funnel, formats spéciaux et schéma conseillé par ligne.
- **Rapport mensuel par script** : `scripts/rapport.py` (clics,
  impressions, marque et hors marque, requêtes nouvelles, bilan du journal
  de mesure, décisions à valider) en Markdown et en JSON stable. La section
  « Lecture et décisions » est conservée d'un passage à l'autre.
- **Données structurées** : `schema_validate.py --socle --strict`, fiches
  entités Wikidata et déploiement dans `seo-schema-jsonld`.
- **Score on-page en 6 catégories** avec malus, mots-clés secondaires et
  mode URL ; composants HTML FAQ, bannière E-E-A-T et bannière contact.
- Brief en 14 sections (création ou optimisation), règles de rédaction
  anti-IA, politique d'occurrences du mot-clé réglable par client.

### Modifié

- `opportunites.py` : une requête visée par une page du journal (colonne
  `requete`, plusieurs requêtes séparées par `|`) n'est plus proposée « à
  créer » ; elle est rattachée à la page, et gelée si la page est en mesure.
- Meta description : zone verte 120-156 caractères partout.
- `share_of_model.py` : gabarits de prompts par langue, analyse des
  homonymes et du côté vendeur, mode `--sans-web` pour la notoriété seule.

## 3.2.0

### Ajouté

- **Classement des opportunités par client** : `scripts/opportunites.py` et
  le skill `seo-opportunites`. Score = clics mensuels gagnables × valeur du
  thème pour le client × facilité ; une action par ligne (title, enrichir,
  renforcer, consolider, créer) ; les pages en cours de mesure exclues ; la
  couverture des thèmes du métier, pour voir ce qui manque au site. Le
  lexique du métier vit dans chaque projet (`memoire/lexique.csv`).
  Utilisé par le cycle d'optimisation et le rapport mensuel.
- **Part de voix IA sur plusieurs moteurs** : `share_of_model.py` interroge
  ChatGPT et Gemini (et Claude, Perplexity si leur clé existe), recherche web
  activée, relève les sources citées et distingue visibilité et réputation.
  Sans dépendance. Perplexity devient facultatif.
- `projet.propriete_gsc` : la propriété Search Console se règle par projet,
  pour qu'un même environnement cloud serve plusieurs clients.


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
