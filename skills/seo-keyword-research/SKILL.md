---
name: seo-keyword-research
description: >
  Recherche de mots-clés complète : expansion sémantique, volumes, difficulté,
  filtrage du bruit, choix du mot-clé pivot, classification par intention et
  par étape du tunnel (TOFU / MOFU / BOFU), risque zero-click IA, opportunité
  GEO, contrôle de cannibalisation par type de page, arbitrage créer /
  optimiser / ignorer, et export pour import en masse. Déclencher sur
  "mots-clés", "keyword research", "recherche de mots-clés", "sur quoi me
  positionner", "volume de recherche", "intention de recherche", "quels
  sujets traiter", "champ sémantique", "requêtes", "mot-clé pivot", "je
  cherche des idées de contenu", "mots-clés faciles", "KD max", "site neuf",
  "DA faible", "difficulté sous 20".
---

# Recherche de mots-clés — arbitrer, pas collectionner

Une liste de 800 mots-clés n'est pas un livrable. C'est une façon de ne rien
décider. Le livrable, c'est **20 requêtes qu'on va travailler et la raison
pour laquelle on ignore les autres**.

## Étape 1 — Le point de départ

Trois sources, dans cet ordre de fiabilité :

1. **Search Console** — ce sur quoi vous êtes déjà vu. La donnée la plus
   fiable qui existe, parce qu'elle est vraie pour *votre* site. Les requêtes
   à impressions et sans clic sont les plus rentables.
2. **Vos concurrents** — leurs mots-clés organiques (Semrush, Ahrefs). Ils
   ont déjà fait le travail de validation du marché.
3. **L'expansion** — `demande.py`, suggestions Google, People Also Ask,
   Reddit.

`demande.py` interroge DataForSEO sans connecteur MCP : il tourne donc aussi
dans une routine cloud (identifiants `DATAFORSEO_LOGIN` / `DATAFORSEO_PASSWORD`).

```bash
# Longue traîne : volume, KD, intention, tendance sur un an
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/demande.py" idees --graines "graine 1, graine 2" --langue fr --mode suggestions
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/demande.py" idees --lexique --langue fr --ecrire   # graines = lexique du projet
# Volumes de requêtes déjà connues
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/demande.py" volumes --mots "requête a, requête b" --langue fr
# SERP d'une requête candidate : top 10, PAA, AI Overview
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/demande.py" serp --mot "requête" --langue fr
```

`--mode proches` élargit aux requêtes sémantiquement voisines ; `--ecrire`
produit `donnees/demande-<langue>-<date>.csv`, que `seo-opportunites` lit
directement. Une passe par langue du projet.

**Avec le MCP Ubersuggest** (dans une session, pas dans une routine
cloud sans connecteur) :
- `auth_status` d'abord : un compte déconnecté se dit, il ne se remplace
  pas par des chiffres supposés ;
- à **chaque** appel, la langue (`language: "fr"`) et le pays (`locId`,
  via `location_suggest`) : sans `locId`, les volumes sont mondiaux, et le
  rapport doit le dire ;
- `keyword_suggestions` pour la longue traîne (questions, comparaisons),
  `keyword_overview` pour volume, difficulté, CPC et tendance,
  `serp_analysis` pour le top 10 ;
- Ubersuggest **n'expose pas la présence d'un AI Overview** : prenez les
  questions remontées par `keyword_suggestions` comme indice de PAA, et
  `brand_visibility_overview` / `brand_prompts` pour la visibilité dans les
  moteurs IA ;
- les réponses brutes se gardent dans un cache du projet (non versionné),
  puis se réduisent au CSV `requete,volume,page` que lit `seo-opportunites`.

**Une requête de Search Console sans volume connu** garde ses impressions
comme borne basse, marquée « estimée » : ce n'est pas un volume de
recherche. Une seconde passe (`demande.py volumes` ou `keyword_overview`)
donne le vrai chiffre.

Reddit mérite un mot : c'est la meilleure source de **vocabulaire réel**.
Les gens y écrivent leurs problèmes avec leurs mots, pas avec les vôtres.
Un mot-clé issu d'un thread Reddit convertit mieux qu'un mot-clé issu d'un
outil.

## Étape 2 — Filtrer le bruit, AVANT tout test de volume

Un volume mesuré sur une requête qui n'est pas pour vous est une donnée
fausse qui a l'air juste. On écarte d'abord, on mesure ensuite :

- **Hors zone** : une requête qui nomme une ville, une région ou un pays où
  le site n'intervient pas est exclue, quel que soit son volume.
- **Appartient à une autre page du site** : c'est de la cannibalisation.
  On la laisse à la page qui la sert déjà (voir étape 8).
- **Au-dessus du plafond de KD** (étape 4) : jamais le pivot d'une page.
  Elle sert de champ sémantique, pas de cible.
- **Bruit Search Console** : requêtes à 1 impression, fautes de frappe
  isolées, requêtes tronquées ou sans sens — ignorées.
- **Termes ambigus** : un sigle ou un mot polysémique du métier (« IA »,
  « GEO », un nom de produit qui est aussi un prénom) ramène des requêtes
  d'un autre univers (géographie, jeux, homonymes). Un terme ambigu n'est
  retenu qu'avec un **mot de contexte** du métier dans la requête, et une
  liste négative (les univers voisins) écarte le reste avant toute mesure.

Chaque exclusion se consigne avec sa raison : c'est ce qui évite de rouvrir
le débat le mois suivant.

## Étape 3 — Enrichir

Pour chaque requête restante : volume mensuel, **tendance sur un an**
(`tendance_an_pct` dans les sorties de `demande.py`), difficulté, CPC (proxy
de valeur commerciale), features SERP présentes, présence d'un AI Overview.

Le CPC est un signal sous-utilisé : un mot-clé à 12 € de CPC vaut de l'argent
même à 90 recherches/mois. Un mot-clé à 0,10 € et 8 000 recherches/mois n'en
vaut souvent aucun.

La **saisonnalité** se lit dans `tendance_an_pct` : une forte variation
annuelle signale une tendance de fond ou un pic saisonnier. Vérifiez le mois
de pic avant de planifier : un contenu saisonnier se publie 6 à 8 semaines
avant son pic, pas pendant.

## Étape 4 — Choisir le mot-clé pivot

Le pivot d'une page = **le meilleur compromis volume × KD bas × intention
commerciale cohérente avec le vrai sujet de la page**. Pas le plus gros
volume : celui qu'on peut réellement gagner et qui mène à ce qu'on vend.

Présentez les candidats **triés par KD croissant**, avec volume, intention
et tendance, puis le pivot retenu et, pour chaque candidat écarté, la raison
en une ligne (« KD 62 à DR 15 », « intention informationnelle sur une page
service », « appartient à une autre page »).

Sur la difficulté : comparez à l'autorité de votre site, pas dans l'absolu.
Un KD 40 est infranchissable à DR 8 et facile à DR 65.

### Le plafond de KD, fixé par l'autorité du domaine

Avant de lister les candidats, lisez l'autorité du domaine
(`seuils.autorite_domaine` de la config ; à défaut, mesurez-la : DR Ahrefs
`site-explorer-domain-rating`, Authority Score Semrush, DA Moz) et déduisez
le plafond :

| Autorité du domaine (DR / DA / AS) | KD maximum d'un mot-clé principal |
|---|---|
| < 20 — site neuf ou peu lié | **20** |
| 20 à 39 | 30 |
| 40 à 59 | 45 |
| ≥ 60 | pas de plafond dur : comparez aux DR du top 10 |

`seuils.kd_max` force le plafond quand il est renseigné. Autorité inconnue
et non mesurable : appliquez le palier « site neuf » et dites-le.

Le plafond est une règle dure, pas une préférence :

- **Aucun mot-clé principal** (page pilier comprise) au-dessus du plafond.
  Une requête plus difficile reste dans le champ sémantique ou dans les
  mots-clés secondaires, et peut être notée « cible à DR X » pour plus tard.
- **Comparez des KD du même outil** que l'autorité : un KD Semrush, un KD
  Ahrefs et une difficulté DataForSEO ne sont pas sur la même échelle.
- KD absent pour une requête : vérifiez la SERP (`seo-serp-analysis`) avant
  de la retenir ; si le top 10 n'est fait que de domaines à forte autorité,
  écartez-la.
- Annoncez le plafond en tête du livrable : « autorité 8 (DR Ahrefs) →
  KD ≤ 20 ».

Quand l'autorité franchit un palier, relevez le plafond et repassez les
requêtes écartées pour cette seule raison : ce sont les prochains pivots.

## Étape 5 — Classer par intention et par étape du tunnel

| Intention | Marqueurs | Ce qu'il faut produire |
|-----------|-----------|------------------------|
| **Informationnelle** | comment, pourquoi, qu'est-ce que, guide | Guide, tutoriel, définition |
| **Commerciale** | meilleur, comparatif, avis, alternative, vs | Comparatif, test, page alternative |
| **Transactionnelle** | acheter, prix, tarif, devis, près de moi | Page produit, service, devis |
| **Navigationnelle** | marque + terme | Page dédiée, ou rien |

**Étiquetage du tunnel**, dans cet ordre : l'URL d'abord, la requête
ensuite, TOFU par défaut.

| Étape | Motifs d'URL | Motifs de requête |
|---|---|---|
| **BOFU** | pricing, tarif, demo, contact, temoignages, services, devis, essai, checkout | prix, acheter, devis, souscrire |
| **MOFU** | comparatif, vs, alternative, use-case, tutoriel, avis, benchmark | comparatif, vs, alternative, avis, différence |
| **TOFU** | blog, guide, glossaire, faq, ressources, conseils, actualites | comment, pourquoi, qu'est-ce que, définition, guide |

**Le mix TOFU / MOFU / BOFU est un paramètre du projet**, pas une règle
universelle :

- **60 / 25 / 15** par défaut pour un **site jeune** qui construit son
  autorité thématique : il faut d'abord exister sur le sujet.
- **40 / 40 / 20** pour un **site établi** qui pousse la conversion.

Il se règle dans `decupler-seo.config.yml` (clé `opportunites.mix`). Erreur
classique dans les deux cas : ne produire que de l'informationnel parce que
c'est là qu'est le volume, puis s'étonner que le trafic ne convertisse pas.

## Étape 6 — Le risque zero-click IA

Une part croissante des requêtes informationnelles reçoit une réponse
directe dans l'AI Overview. Vous êtes cité, on ne clique pas.

| Risque | Type de requête | Décision |
|--------|-----------------|----------|
| 🔴 Élevé | Fait simple : « qu'est-ce que le SEO », conversions, définitions | **Ne créez pas de page dédiée.** Traitez-le en section d'une page plus large |
| 🟡 Moyen | Procédural, multi-dimensionnel : « comment choisir un CRM » | Créez, mais avec de la profondeur que l'IA ne peut pas résumer |
| 🟢 Faible | Local, temps réel, avis, données propriétaires, comparaison nuancée, transactionnel | **Créez en priorité.** Le clic reste |

Un plan éditorial rempli de « qu'est-ce que X » est aujourd'hui un plan à
trafic nul. `demande.py serp` dit si un AI Overview est présent.

## Étape 7 — L'opportunité GEO

Un mot-clé peut avoir peu de clics et beaucoup de valeur, s'il vous fait
citer par les moteurs IA auprès d'acheteurs. Notez chaque requête de 1 à 5 :

- Est-ce une question qu'un décideur pose à ChatGPT avant d'acheter ?
- La réponse actuelle des LLM est-elle mauvaise ou incomplète ?
- Avez-vous une donnée propriétaire à apporter ?

Un 5/5 en GEO avec 40 recherches/mois peut valoir plus qu'un 3 000/mois
informationnel saturé.

## Étape 8 — Cannibalisation : à chaque type de page ses requêtes

Avant d'attribuer une requête à une page, vérifiez qu'aucune autre ne la
sert déjà (Search Console : quelle URL reçoit les impressions). Règles par
type de page :

- **Portfolio / réalisations ≠ pages secteur ou service** : une réalisation
  illustre et renvoie vers la page service ; elle ne vise pas sa requête.
- **Carrières / recrutement ≠ requêtes commerciales** : « métier + ville »
  peut être une recherche d'emploi ou de prestataire. La SERP tranche, et la
  page carrières ne prend que la première.
- **Blog en soutien des piliers** : un article vise une question précise et
  lie vers le pilier ; il ne cible jamais la requête du pilier.

Les risques repérés vont dans une **note séparée**, pas dans la liste
d'import.

## Étape 9 — Décider

Trois piles, et on assume la troisième :

**🔴 À FAIRE MAINTENANT** — bonne intention, difficulté atteignable,
zero-click faible, valeur business réelle. Maximum 20 lignes.

**🟡 À FAIRE AVEC UN ANGLE** — le volume est là mais la SERP est saturée ou
le zero-click est élevé. Précisez l'angle qui vous rend citable : donnée
originale, format différent, niche plus étroite.

**⚫ À IGNORER** — trop difficile pour votre autorité actuelle, hors
proposition de valeur, ou tellement zero-click qu'il n'y a rien à gagner.
**Dites pourquoi.** C'est la partie la plus utile du livrable.

**Écarts avec les concurrents (gap)** : ne retenez que les requêtes à
**volume ≥ 30 et KD ≤ 80**. Une requête est **couverte** si son slug (en
minuscules, sans accents, espaces en tirets) est égal à un segment d'URL du
site ; sinon c'est un gap, à vérifier à la main avant de conclure à une page
manquante — une page peut couvrir la requête sous un autre slug.

## Étape 10 — Regrouper en clusters

Ne créez pas une page par mot-clé. Regroupez les requêtes qui partagent la
même intention et la même SERP (si le top 10 est identique à 60 %, c'est la
même page).

Par cluster : la requête principale, les 5-15 secondaires, la page cible
(existante ou à créer), le type de page, l'étape du tunnel, la priorité.

## Export pour import en masse

Les outils tiers (suivi de positions, clustering, planification) importent
des listes plates. Livrez :

- **Liste plate** : un mot-clé par ligne, sans en-tête, sans colonne.
- **Format silo** : une ligne par silo, `[Silo] / mot-clé 1 / mot-clé 2 / mot-clé 3`.
- **Risques de cannibalisation** : dans une note à part, jamais mêlés à la
  liste.

## Livrables

- `MOTS-CLES.md` — pivot par page, les 3 piles, les exclusions justifiées
- `mots-cles.csv` — tableau complet : requête, volume, KD, CPC, tendance,
  intention, tunnel, zero-click, GEO, cluster, décision
- `CLUSTERS.md` — l'architecture éditoriale qui en découle
- `import-mots-cles.txt` et `import-silos.txt` — pour les outils tiers
- `cannibalisation.md` — les risques repérés

Enchaînez : `/seo cocon` pour l'architecture, `/seo brief` pour produire,
`seo-opportunites` pour prioriser.
