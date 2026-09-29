---
name: seo-brief
description: >
  Produit un brief SEO consolidé en 14 sections, en deux variantes :
  CRÉATION d'une page neuve ou OPTIMISATION d'un contenu existant (verdict,
  décisions structurelles section par section). Données d'abord (SERP live,
  PAA, AI Overview, Search Console, cannibalisation), puis intention, X-Ray
  du top 5, information gain, mix de mots-clés, noyau sémantique, H1 et
  intro rédigés, plan Hn détaillé, prompts GEO, maillage et priorités
  chiffrées. Déclencher sur "brief", "brief SEO", "brief rédactionnel",
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
| **CRÉATION** | la page n'existe pas | 0 à 13, **sans 2 ni 9** |
| **OPTIMISATION** | une URL sert déjà l'intention | 0 à 13, toutes |

Fichier produit, dans un projet : `recherche/briefs/<slug>.md`.

**Les verdicts sont tranchés.** Jamais « envisager », « on pourrait »,
« éventuellement ». Chaque ligne dit quoi faire : le rédacteur n'arbitre pas,
il exécute.

## Étape 0 — les données avant le brief

**Ne rédigez jamais un brief sans avoir regardé la SERP.** C'est la
différence entre un brief et une supposition.

1. **SERP live**, dans chaque langue du projet :
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/demande.py" serp --mot "<mot-clé>" --langue fr
   ```
   Top 10 organique, questions « Autres questions posées », présence d'un AI
   Overview, recherches associées (~0,002 $ l'appel). Fonctionne sans
   connecteur, donc aussi dans une routine.
2. **Secondaires et longue traîne**, avec volume, KD, intention et tendance :
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/demande.py" idees --graines "<mot-clé>, <variante>" --langue fr
   ```
3. **Top 5 réellement lu** (Firecrawl) : plans Hn, angles, preuves, longueur.
   Pas résumé de mémoire.
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
renvoie vers elle (décision DÉPLACER en section 9, ou ligne en section 13).

## Les 14 sections

### 0. Paramètres du contenu

| Paramètre | Valeur |
|---|---|
| Mot-clé principal | + volume, KD |
| Mot-clé secondaire | + volume, KD |
| URL cible | existante, ou proposée : courte, descriptive, avec le mot-clé |
| Objectif | trafic, lead, vente, citation IA |
| Nombre de mots cible | fourchette tirée du top 5, jamais un objectif de remplissage |
| Tonalité / style | repris de `projet.ton` |
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

| Source | Angle | Structure Hn | Point fort | Faille à exploiter |
|---|---|---|---|---|

Sous le tableau : **AI Overview présent ?** oui/non, et quelles sources il
cite. Type de pages qui rankent, features occupées (PAA, vidéo, pack local),
fourchette de longueur.

### 4. Différenciation (information gain)

- **L'angle unique en une phrase** : ce que cette page apporte que le top 10
  n'apporte pas. Si vous ne savez pas l'écrire, ne produisez pas la page.
- **3 à 5 axes de valeur** : donnée propre, cas vécu, outil, grille de
  décision, cas particuliers. Ils alimentent la grille de `seo-benchmark`
  (au moins 5 axes gagnés avant publication).

### 5. Mix de mots-clés

| Priorité | Mot-clé | Section d'intégration |
|---|---|---|
| Principal | | H1, intro, un H2, CTA final |
| Secondaire | | |
| HAUTE | | |
| MOYENNE | | |
| COMPLÉMENTAIRE | | |

Règle : **chaque terme HAUTE comble une lacune relevée en section 2** (en
CRÉATION : une faille de la section 3). Un terme HAUTE sans lacune
correspondante descend en MOYENNE.

### 6. Noyau sémantique — 15 à 20 termes

Trois grappes, une par moment de la recherche :

- **Know** — comprendre : définitions, mécanismes, règles, questions PAA.
- **Why / When / Feel** — se reconnaître : points de douleur, situations
  déclenchantes, craintes et objections, longue traîne conversationnelle.
- **Do** — agir : verbe + mot-clé, étapes, coûts, délais, termes
  techniques, choix d'un prestataire.

Plus : **entités nommées obligatoires** (organismes, normes, lois, outils,
lieux — ce que le Knowledge Graph relie au sujet) et **glossaire métier**
(le terme juste et son usage). Pas pour les caser : pour vérifier qu'aucun
sous-sujet n'est oublié. Export : `champ-semantique.csv`.

### 7. H1 & introduction

`DÉCISION : MODIFIER / GARDER / ENRICHIR`

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

Ton et registre (`projet.ton`), vouvoiement ou tutoiement, paragraphes de 3
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
- 2-3 sources externes d'autorité, et le schema à poser (Article, FAQPage,
  Service, HowTo…) avec `seo-schema-jsonld`.

### 13. Priorités

**Modifications CRITIQUES — impact SEO X/10**
1. …

**Modifications IMPORTANTES — impact SEO X/10**
1. …

Le GAP CRITIQUE de la section 2 figure toujours en tête des critiques.

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

- `recherche/briefs/<slug>.md` — le brief complet
- `champ-semantique.csv` — noyau sémantique et entités
- Le H1, l'introduction et la FAQ **déjà rédigés** — pas à faire par le
  rédacteur

Enchaînez : `seo-benchmark` pour valider les axes, puis `/seo article`
(`seo-redaction`) pour la rédaction.
