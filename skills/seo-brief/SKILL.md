---
name: seo-brief
description: >
  Produit un brief SEO/GEO consolidé en 18 sections, en deux variantes :
  CRÉATION d'une page neuve ou OPTIMISATION d'un contenu existant (verdict,
  décisions structurelles section par section). Données d'abord (SERP live
  DataForSEO ou repli Firecrawl, top 5 lu et mesuré : Hn, longueur, entités,
  formats, FAQ, schémas, médias ; PAA, AI Overview, Search Console,
  cannibalisation, style mesuré du client, sitemap), puis intention, X-Ray
  du top 5, gap et information gain, mix de mots-clés, noyau sémantique et
  entités, réponse directe, H1 et intro rédigés, plan Hn chiffré, FAQ
  rédigée, prompts IA et fan-out, données structurées, sources E-E-A-T,
  checklist GEO, maillage et priorités chiffrées. Déclencher sur "brief", "brief SEO", "brief rédactionnel",
  "brief d'optimisation", "plan d'article", "plan Hn", "que dois-je écrire
  sur", "cahier des charges rédaction", "structure d'article", "je veux
  écrire sur", "optimiser ce contenu existant".
---

# Brief SEO consolidé — le document qui rend la page inévitable

Un bon brief permet à quelqu'un qui ne connaît rien au SEO d'écrire une page
qui ranke et se fait citer. S'il faut du jugement SEO pour l'exécuter, le
brief est incomplet.

**Deux variantes, une seule structure :**

| Variante | Quand | Sections |
|---|---|---|
| **CRÉATION** | la page n'existe pas | 0 à 17, **sans 2 ni 9** |
| **OPTIMISATION** | une URL sert déjà l'intention | 0 à 17, toutes |

Fichier produit, dans un projet : `recherche/briefs/<slug>.md`.

**Les verdicts sont tranchés.** Jamais « envisager », « on pourrait »,
« éventuellement ». Chaque ligne dit quoi faire : le rédacteur n'arbitre pas,
il exécute.

## Étape 0 — les données avant le brief

**Ne rédigez jamais un brief sans avoir regardé la SERP.** C'est la
différence entre un brief et une supposition.

1. **SERP live et top 5 lu**, dans chaque langue du projet :
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/serp_concurrents.py" --mot "<mot-clé>" --langue fr
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/serp_concurrents.py" --mot "<mot-clé>" --url <URL existante>   # OPTIMISATION
   ```
   Une SERP DataForSEO (top 10, PAA dépliées, AI Overview et ses sources,
   recherches associées, features ; 0,002 à 0,004 $), puis les 5 premières
   pages concurrentes lues une à une. Sans connecteur, donc aussi dans une
   routine. Deux fichiers dans `recherche/` :
   - `serp-<slug>-<date>.md` — les mesures : longueur (médiane et 3e
     quartile), plans Hn, sujets de H2 récurrents, questions marquées
     « traitée par le top : oui / non », extrait et sources de l'AI
     Overview, champ sémantique commun, ton du top ; avec `--url`, ce qui
     manque à la page du client (sujets, questions, termes, longueur) ;
   - `serp-<slug>-<date>-contenus.md` — le contenu de chaque concurrent,
     titres et listes conservés. **Lisez-le** : angles, preuves et failles
     ne se mesurent pas, ils se lisent.

   Une page illisible (403, rendu JavaScript) est signalée, pas inventée :
   `--repli-dataforseo` la relit par DataForSEO (payant, coût affiché), ou
   lisez-la avec Firecrawl.

   **Quelle source pour la SERP** — la première qui répond, dans cet ordre :

   | Source | Ce qu'elle donne | Ce qui reste à relever |
   |---|---|---|
   | DataForSEO (`serp_concurrents.py`) | top 10, PAA, AI Overview et ses sources, features | rien |
   | MCP Firecrawl (`firecrawl_search`, puis `firecrawl_scrape` sur le top 5, formats `markdown` + `html`) | top organique, pages rendues (JavaScript compris) | PAA, AI Overview, features : **non mesurés** |
   | MCP Ubersuggest (`serp_analysis`, `locId` du pays) | top 10 avec trafic et autorité des domaines | PAA, AI Overview |
   | Aucune | — | lecture manuelle de la SERP, signalée en tête du brief |

   Avec Firecrawl, enregistrez les réponses (`serp.json`, `pages.json` :
   `[{"url", "html", "markdown"}]`) et passez-les au même script, qui
   produit le même rapport sans DataForSEO :
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/serp_concurrents.py" --mot "<mot-clé>" --langue fr \
       --serp-firecrawl serp.json --pages-json pages.json --questions paa.txt
   ```
   `paa.txt` : une question par ligne, relevée ailleurs (PAA vues à la
   main, questions Ubersuggest `keyword_suggestions`, Search Console). Ce
   que la source ne donne pas s'écrit **non mesuré**, jamais « absent ».

   Le rapport mesure, page par page : title, meta, plan H1-H3, mots,
   listes, tableaux, FAQ, schémas, images et vidéos, liens, dates, ton,
   **entités nommées** (noms propres, outils, sigles ; celles que 2 pages
   ou plus citent forment le socle), puis le champ sémantique commun.
2. **Secondaires et longue traîne**, avec volume, KD, intention et tendance :
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/demande.py" idees --graines "<mot-clé>, <variante>" --langue fr
   ```
   Sans DataForSEO : MCP Ubersuggest `keyword_overview` et
   `keyword_suggestions` avec le `locId` du pays (`location_suggest` pour
   le trouver ; sans `locId`, les volumes sont mondiaux : le dire). Un
   volume qu'aucun appel n'a renvoyé s'écrit `n.d.`.
3. **Style de la maison** : `memoire/style.md`. S'il manque, mesurez-le sur
   5 à 10 pages écrites par le client (articles, pages de service) :
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/style_maison.py" <url1> <url2> …
   ```
4. **Existant** (variante OPTIMISATION) : contenu actuel de l'URL et ses
   requêtes Search Console sur 90 jours :
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gsc.py" perf --par query --jours 90 --json
   ```
   Les requêtes à impressions sans clic de cette page nourrissent les
   sections 5 et 8.
5. **Contrôle de cannibalisation** — voir plus bas. Avant toute création.
6. **Vocabulaire réel de l'audience** : Reddit, forums, avis clients.
7. **Positionnement et contraintes** : `decupler-seo.config.yml` → `projet`,
   `memoire/faits.md` (chiffres vérifiés), gabarit CMS de la page.
8. **Pages internes à lier** : le sitemap du client, lu par le même
   script, sort les pages dont l'adresse parle du sujet (section 12) :
   `serp_concurrents.py … --sitemap https://<domaine>/sitemap.xml`.
9. **Prompts IA** : les relevés de `geo-share-of-model`
   (`releves-ia-<mois>.csv`) ou du MCP Ubersuggest (`brand_prompts`) s'ils
   existent pour ce sujet ; sinon les prompts de la section 13 sont des
   **formulations proposées, non mesurées**, à relever avant publication.

**Mode dégradé.** Si les métriques ou la SERP ne remontent pas (identifiants
absents, API en erreur, scraping bloqué), le brief est **produit quand
même** : chaque valeur manquante s'écrit `n.d.`, et la section concernée
s'appuie sur ce qui reste (Search Console, lecture manuelle du top 5, PAA
visibles). Jamais bloqué, jamais d'estimation déguisée en donnée.

## Contrôle de cannibalisation — deux issues

Cherchez ce que le site dit déjà sur l'intention : pages publiées, titres
Hn, requêtes Search Console qui y mènent. Si une URL sert déjà la même
intention :

- **Option A — reprendre l'URL existante** (par défaut) : le brief passe en
  variante OPTIMISATION. L'URL garde son historique et ses liens.
- **Option B — URL distincte**, seulement si l'intention diffère réellement
  (autre étape du parcours, autre public) : angle et H1 qui ne visent pas la
  requête de l'autre page, lien croisé dans les deux sens, canonical si les
  contenus se recouvrent.

Consignez l'option retenue et sa raison en tête du brief.

## Contrainte de gabarit CMS

Une page de service ou de catégorie vit dans un gabarit : blocs fixes (hero,
réassurance, formulaire, CTA), emplacements limités. Le brief s'y plie.
**Ce qui n'entre pas dans le gabarit ne se force pas** : un développement
pédagogique trop long pour une page service devient un article de blog qui
renvoie vers elle (décision DÉPLACER en section 9, ou ligne en section 17).

## Les 18 sections

### 0. Paramètres du contenu

| Paramètre | Valeur |
|---|---|
| Mot-clé principal | + volume, KD |
| Mot-clé secondaire | + volume, KD |
| URL cible | existante, ou proposée : courte, descriptive, avec le mot-clé |
| Objectif | trafic, lead, vente, citation IA |
| Nombre de mots cible | fourchette **mesurée** : médiane → 3e quartile du top (rapport SERP), jamais un objectif de remplissage |
| Tonalité / style | `memoire/style.md` (mesuré), à défaut `projet.ton` |
| Langue | une ligne par langue si le projet est multilingue |
| Gabarit CMS | type de page et ses blocs fixes |

### 1. Intention & public cible

- **Intention dominante** en une phrase, justifiée par ce que montre la SERP.
- **Sous-intention** si la SERP est hybride (« comprendre » + « trouver un
  prestataire »).
- **Persona** : qui cherche, dans quelle situation, avec quelle crainte.
- **Objectif hybride** : comment l'information mène à l'action sans rupture
  commerciale. La page répond d'abord ; l'appel à l'action arrive comme la
  suite logique de la réponse, pas comme une publicité.

### 2. Diagnostic de l'existant *(OPTIMISATION seulement)*

`VERDICT GLOBAL : À AJUSTER / BON SOCLE / À REFONDRE`

- **GAP CRITIQUE** : le H2 manquant le plus coûteux, celui que le top 5
  traite et pas vous. Une ligne, en tête de section.
- Écarts avec le top de la SERP : sujets, preuves, formats absents.
- Lacunes sémantiques : termes et entités du noyau (section 6) absents.
- Sections manquantes.
- **Éléments nuisibles** : marqueurs d'écriture générée, introduction
  théorique, conditionnel de distance (« pourrait », « serait »),
  formulations impersonnelles, chiffres sans source.

### 3. X-Ray SERP — top 5

| # | Source | Mots | H2 / H3 | Formats (listes, tableaux, FAQ) | Schémas | Médias | Angle | Point fort | Faille à exploiter |
|---|---|---|---|---|---|---|---|---|---|

Sous le tableau, les **entités** que le top cite (au moins 2 pages) et
celles qu'une seule page apporte. Structure, longueur, formats, schémas,
médias, entités et date viennent du rapport SERP ; angle,
point fort et faille, de la lecture de `-contenus.md`. Sous le tableau :
**AI Overview présent ?** oui/non, quelles sources il cite, et ce que dit
son extrait — c'est la réponse que l'IA retient déjà : la page la couvre
**et** va plus loin. Type de pages qui rankent, features occupées (PAA,
vidéo, pack local), fourchette de longueur.

### 4. Différenciation (information gain)

- **L'angle unique en une phrase** : ce que cette page apporte que le top 10
  n'apporte pas. Si vous ne savez pas l'écrire, ne produisez pas la page.
- **Où le chercher dans le rapport SERP** : les questions « traitée par le
  top : **non** », les sujets qu'une seule page traite, ce que l'extrait de
  l'AI Overview ne dit pas. Ce que tout le top fait (sujets récurrents) est
  le ticket d'entrée, pas la différence.
- **Matrice de gap** : une ligne par sujet ou question qui compte, une
  colonne par page du top (✓ / —), une colonne « nous ». Ce que tout le
  monde couvre = socle ; ce que 1 page couvre = piste ; ce que **personne**
  ne couvre et qui sert l'intention = angle différenciant.

  | Sujet / question | #1 | #2 | #3 | #4 | #5 | Nous |
  |---|---|---|---|---|---|---|

- **3 à 5 axes de valeur** : donnée propre, cas vécu, outil, grille de
  décision, cas particuliers. Ils alimentent la grille de `seo-benchmark`
  (au moins 5 axes gagnés avant publication).

### 5. Mix de mots-clés

| Priorité | Mot-clé | Volume · KD (source) | Section d'intégration |
|---|---|---|---|
| Principal | | | H1, intro, un H2, CTA final |
| Secondaire | | | |
| HAUTE | | | |
| MOYENNE | | | |
| COMPLÉMENTAIRE | | | |
| Longue traîne | requêtes de 4 mots et plus, questions | | H3, FAQ |

Règle : **chaque terme HAUTE comble une lacune relevée en section 2** (en
CRÉATION : une faille de la section 3). En OPTIMISATION, les « termes du
top absents de la page » du rapport `--url` sont les premiers candidats. Un terme HAUTE sans lacune
correspondante descend en MOYENNE.

### 6. Noyau sémantique — 15 à 20 termes

Trois grappes, une par moment de la recherche :

- **Know** — comprendre : définitions, mécanismes, règles, questions PAA.
- **Why / When / Feel** — se reconnaître : points de douleur, situations
  déclenchantes, craintes et objections, longue traîne conversationnelle.
- **Do** — agir : verbe + mot-clé, étapes, coûts, délais, termes
  techniques, choix d'un prestataire.

Point de départ : le **champ sémantique commun** du rapport SERP (termes
présents sur au moins la moitié du top) et ses questions. Triez, ne
recopiez pas : un terme de navigation ou une marque concurrente n'a rien à
faire dans le noyau.

Plus : **entités nommées obligatoires** (organismes, normes, lois, outils,
lieux — ce que le Knowledge Graph relie au sujet) et **glossaire métier**
(le terme juste et son usage). Pas pour les caser : pour vérifier qu'aucun
sous-sujet n'est oublié. Export : `champ-semantique.csv`.

### Triplets et entités

Le brief liste les **triplets à affirmer** : 3 à 8 faits sous la forme
sujet — prédicat — objet, avec leur source et leur emplacement (réponse
directe, H2, FAQ), tirés de `memoire/triplets.csv` pour cette page ; un
fait absent du registre n'entre qu'avec une source nommée. Il liste aussi
les entités principales avec leur QID (`memoire/entites.csv`) et celle qui
va en `about`. Méthode, gabarit de la section et contrôle :
`seo-entites-triplets` (`scripts/triplets.py verifier`).

### 7. H1, réponse directe & introduction

`DÉCISION : MODIFIER / GARDER / ENRICHIR`

- **Réponse directe RÉDIGÉE, 40 à 60 mots**, placée juste sous le H1 :
  le sujet nommé en première phrase (« Un audit GEO est… »), une réponse
  complète à la requête principale (définition, chiffre ou verdict), aucun
  pronom sans référent, compréhensible copiée seule. C'est le passage que
  l'AI Overview, ChatGPT ou Perplexity reprennent. Comptez les mots.

- ❌ H1 actuel : « … »
- ✅ H1 proposé : 50-60 caractères, mot-clé en tête, année si le sujet
  vieillit. Proche du title, pas identique.
- **Title** 50-60 caractères, **meta** 120-156 caractères (promesse +
  différenciation), ou renvoi à `seo-meta-serp`.
- **Introduction RÉDIGÉE**, 80-100 mots, selon une méthode nommée dans le
  brief — **PAS** (problème, agitation, solution), **AIDA**, ou
  **storytelling** (accroche, problème, annonce). Mot-clé dans la première
  phrase, départ d'une situation concrète du lecteur, et une réponse directe
  extractible telle quelle par un LLM ou un featured snippet avant la fin de
  l'intro. Jamais une définition de dictionnaire. Le rédacteur ne la réécrit
  pas.

### 8. Plan Hn détaillé

**Construire le plan à partir du rapport SERP, dans cet ordre :**

1. **Le socle** : les sujets récurrents (traités par au moins 2 pages du
   top). Google les attend. Un sujet récurrent écarté l'est par écrit, avec
   sa raison (hors intention, hors gabarit).
2. **Les gaps** : les questions PAA qu'aucun titre du top ne traite, un
   sujet isolé qui sert l'intention, et le H2 d'information gain
   (section 4).
3. **L'ordre** : celui du lecteur (comprendre → se reconnaître → agir),
   jamais celui d'un concurrent.
4. **Le volume** : le nombre de H2 suit la médiane du top, entre 5 et 8 ;
   les mots par section se répartissent dans la fourchette de la section 0.

5 à 8 H2, 2 à 3 H3 au plus par H2. Pour chaque H2 :

- **Intention** de la section, en une ligne.
- **Décision / existant** (OPTIMISATION) : ce qui est gardé, ce qui change.
- **Directives** : ce que la section contient ; la donnée, l'exemple ou la
  source à y placer ; le nombre de mots approximatif.
- **Format** : paragraphe + liste (cible featured snippet), pas-à-pas,
  tableau comparatif, encadré « conseil » ou « attention ».
- **Visuel** : tableau, schéma, capture, photo de terrain — et pourquoi.
- **Mots-clés** de la section 5 à y intégrer.
- **Marqueurs stylistiques** : anecdote, question au lecteur, phrase courte
  de rupture.

Règles de forme :

- **H2 formulé en question**, suivi d'une **réponse directe de 1 à 3
  phrases** avant tout développement.
- **Un H2 « différenciation / expert »** porte l'information gain de la
  section 4 : la donnée propre, la méthode, le retour de terrain.
- **Prompts GEO ciblés** : pour chaque section, la question conversationnelle
  qu'un utilisateur poserait à ChatGPT ou Perplexity, et à laquelle la
  section répond **dès ses premières lignes**.
- **FAQ** : 3 à 5 vraies questions PAA (issues de `demande.py serp` ou de
  Search Console), réponses de 2 à 4 lignes dont la première phrase répond.
  Rédigées dans le brief.
- **Conclusion** : les points clés en 3 lignes, puis un **CTA lié à
  l'objectif** de la section 0, avec le libellé exact du bouton ou du lien.
- **Définitions** explicites et autonomes : « X est un… qui… ».
- **Statistique citable** : au moins une donnée chiffrée sourcée, idéalement
  propriétaire.

### 9. Décisions structurelles *(OPTIMISATION seulement)*

| Section existante | Décision | Action |
|---|---|---|
| | GARDER & ENRICHIR | |
| | RENOMMER & RESTRUCTURER | |
| | SUPPRIMER | |
| | DÉPLACER | vers un article de blog si hors gabarit |
| | FUSIONNER & RÉDUIRE | |
| | CRÉER ⭐ | |

Chaque section existante a sa ligne. Aucune n'est laissée sans décision.

### 10. Style & formatage

Les **règles déduites** de `memoire/style.md` (adresse au lecteur,
personne, longueur des phrases et des paragraphes, questions, listes) et sa
section « Lecture » ; à défaut `projet.ton`. Le ton du top, dans le rapport
SERP, dit le registre que la SERP récompense ; il ne remplace jamais la voix
du client. Puis : paragraphes de 3
à 4 lignes, listes de 6 puces au plus, une idée neuve par paragraphe,
tableau obligatoire dès que l'information est comparative ou chiffrée.
Formules interdites propres au projet : `regles.interdits`.

### 11. Anti-détection IA

Renvoi aux règles de `seo-redaction` (anti-détection, interdits éditoriaux,
relecture). Ajoutez seulement ce qui est propre à ce contenu : l'anecdote de
terrain à raconter, la position assumée, le contre-argument à traiter.

### 12. Maillage interne

| Ancre exacte | Page cible | Contexte (phrase ou section) |
|---|---|---|

- **3 à 6 liens sortants minimum**, dans cet ordre de priorité : pilier ou
  page service du cluster → pages de conversion → contenus satellites.
- Les pages qui devront lier **vers** ce contenu une fois publié.
- **Ne jamais supprimer un lien interne existant** : on en ajoute.
- **Pages cibles réelles** : tirées du sitemap (`--sitemap`, section
  « Maillage interne » du rapport SERP) ou de l'inventaire du projet,
  jamais une adresse supposée. Sans sitemap lisible, écrivez-le.
- Sources externes : section 15 ; schema : section 14.

### 13. Prompts IA & fan-out

La requête Google n'est pas la question posée à une IA. Listez :

- **5 à 10 prompts neutres** (sans la marque) tels qu'un utilisateur les
  tape dans ChatGPT, Perplexity ou Gemini : conversationnels, en
  situation (« Je dirige une PME, comment savoir si ChatGPT parle de mon
  entreprise ? »). Pour chacun : mesuré (relevé, date, marques citées) ou
  **proposé, non mesuré**.
- **Le fan-out** : les 6 à 10 sous-questions qu'un moteur génératif
  décompose pour répondre (prix, délai, pour qui, étapes, outils,
  comparatif, risques, alternatives). Pour chacune, la section du plan qui
  y répond **dans ses premières lignes**. Une sous-question sans section
  = un H2 ou une question de FAQ à ajouter. Objectif : 100 % couvertes
  (le seuil `geo-ready` est 70 %).

| Sous-question (fan-out) | Section qui répond | Couverte par le top ? |
|---|---|---|

### 14. Données structurées recommandées

Le `@graph` de la page, nœud par nœud, avec `seo-schema-jsonld` :
`WebPage` (ou `Article` / `BlogPosting`, `Service` pour une offre) +
`BreadcrumbList` + `FAQPage` si la FAQ est visible + `Person` (auteur) +
`Organization`. `about` et `mentions` portent les entités de la section 6
(avec QID Wikidata). Indiquez ce que le top utilise (rapport SERP) et ce
qui manque. **Jamais un schéma qui affirme ce que la page ne montre pas.**

### 15. Sources & E-E-A-T à apporter

- **Sources externes** (2 à 4) : institution, étude, norme, documentation
  officielle d'un moteur — avec leur lien, jamais un concurrent direct.
- **Preuves propriétaires** : chiffre interne, cas client, capture,
  méthode maison (`memoire/faits.md`). Ce qui manque s'écrit
  `[À COMPLÉTER : …]`, jamais inventé.
- **Auteur** : nom, rôle, expérience vécue sur le sujet, page auteur ;
  date de publication et de mise à jour visibles. Grille : `seo-eeat`.

### 16. Checklist GEO avant publication

- [ ] Réponse directe de 40-60 mots sous le H1, sujet nommé
- [ ] Chaque H2 formulé comme une question ou une intention, réponse en 1-3 phrases dessous
- [ ] Premier paragraphe de chaque H2 compréhensible seul (40-120 mots)
- [ ] Définition explicite « X est un… qui… »
- [ ] Au moins une donnée chiffrée sourcée et datée, idéalement propriétaire
- [ ] Tableau dès qu'il y a comparaison ou chiffres ; liste numérotée pour les étapes
- [ ] FAQ de 3 à 6 questions réelles, réponses de 40-60 mots
- [ ] Fan-out couvert (section 13)
- [ ] Marque nommée à côté de son expertise dans les passages clés
- [ ] Auteur identifié, dates visibles, `dateModified` cohérent
- [ ] JSON-LD valide (`schema_validate.py`) et conforme au contenu visible
- [ ] Contenu lisible sans JavaScript ; robots.txt ouvert aux robots IA (`geo-llms-txt`)
- [ ] Prompts de la section 13 relevés avant publication, puis à J+30 (`geo-share-of-model`)

### 17. Priorités

**Modifications CRITIQUES — impact SEO X/10**
1. …

**Modifications IMPORTANTES — impact SEO X/10**
1. …

Le GAP CRITIQUE de la section 2 figure toujours en tête des critiques.

## Traçabilité — chaque chiffre a son origine

En tête du brief, un bloc **Sources de données** : pour chaque mesure
(volume, KD, positions, longueurs, PAA, AI Overview), l'outil appelé, la
date et le paramètre de lieu. Une valeur qu'aucun appel n'a renvoyée
s'écrit `n.d.` ou **non mesuré**. Les noms des concurrents restent dans le
brief (section 3) et **jamais dans la page**.

---

Pied de brief : `Brief SEO consolidé — [site] — [mot-clé] — [date]`

## Ce qui distingue un brief exploitable

| ❌ Brief inutile | ✅ Brief exploitable |
|------------------|---------------------|
| « Parler des avantages » | « 4 avantages, un paragraphe chacun, avec un chiffre par avantage. Les concurrents n'en citent que 2. » |
| « Article de 2 000 mots » | « Le top 5 fait 1 400-2 600 mots. Écrivez ce que le sujet exige, sans remplissage. » |
| « Optimiser pour le SEO » | « Mot-clé dans le H1, la première phrase, un H2 et le CTA final ; densité 1,5-2,5 %. » |
| « Ajouter une FAQ » | « 4 questions, les voici, réponses de 2 à 4 lignes. » |
| « Envisager de revoir l'intro » | « DÉCISION : MODIFIER. Nouvelle intro ci-dessous. » |

## Sources à citer

Listez-les dans le brief, avec leur lien : textes officiels, organismes,
études, et les chiffres de `memoire/faits.md`. Un chiffre sans source ne
s'écrit pas — ni dans le brief, ni dans la page.

## Livrables

- `recherche/briefs/<slug>.md` — le brief complet, qui cite en tête le
  rapport SERP dont il part (`recherche/serp-<slug>-<date>.md`)
- `champ-semantique.csv` — noyau sémantique et entités
- Le H1, la réponse directe (40-60 mots), l'introduction et la FAQ
  **déjà rédigés** — pas à faire par le rédacteur

Enchaînez : `seo-benchmark` pour valider les axes, puis `/seo article`
(`seo-redaction`) pour la rédaction.
