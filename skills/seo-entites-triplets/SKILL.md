---
name: seo-entites-triplets
description: >
  Rend les connaissances clés d'une page extractibles par les moteurs IA et
  les graphes de connaissances : chaque fait énoncé en triplet explicite
  (sujet — prédicat — objet), une idée par phrase, près du haut ; chaque
  entité reliée à un identifiant stable (Wikidata, site officiel) par le
  JSON-LD (about, mentions, sameAs, DefinedTerm, knowsAbout, provider,
  author) ; une seule valeur par sujet et prédicat sur tout le site. Registre
  du projet (memoire/entites.csv, memoire/triplets.csv), contrôle par script,
  mode automatique pour les routines. Déclencher sur "triplets", "triplets
  sémantiques", "entités", "entités nommées", "knowledge graph", "graphe de
  connaissances", "saillance", "salience", "cohérence des faits",
  "contradictions entre pages", "chiffres différents selon les pages",
  "sameAs", "QID", "Wikidata", "DefinedTerm", "knowsAbout", "about /
  mentions", "faits clés", "extractibilité", "trio sémantique", "Google ne
  sait pas qui on est", "ChatGPT ne nous cite pas comme expert", "page
  auteur", "entity home".
---

# Triplets et entités — dire une chose, une fois, de la même façon partout

Un moteur IA ne lit pas une page comme un lecteur. Il en extrait des faits,
et un fait extrait a toujours la même forme : **un sujet, un prédicat, un
objet**. « Atlas Conseil — est situé à — Lyon. » « Le bilan annuel — coûte —
1 200 € HT. » Une page qui énonce ses faits sous cette forme se fait
reprendre. Une page qui les noie dans des pronoms, des tournures vagues ou
des chiffres qui changent d'une page à l'autre se fait paraphraser, mal, ou
ignorer.

Le travail tient en trois couches, qui se contrôlent chacune par script :

| Couche | Ce qu'on fait | Contrôle |
|--------|---------------|----------|
| **Le texte** | Chaque fait clé en triplet explicite, une idée par phrase, près du haut | `triplets.py extraire` / `verifier` |
| **Le balisage** | Chaque entité principale reliée à un identifiant stable (QID Wikidata, site officiel) | `triplets.py verifier` + `schema_validate.py` |
| **Le site** | Une seule valeur par sujet + prédicat, sur toutes les pages, dans toutes les langues | `triplets.py coherence` |

L'exemple fil rouge est fictif : **Atlas Conseil**, cabinet d'expertise
comptable à Lyon.

## 1. Le triplet — écrire des faits extractibles

| Sujet | Prédicat | Objet |
|-------|----------|-------|
| Atlas Conseil | est | un cabinet d'expertise comptable à Lyon |
| Atlas Conseil | accompagne | les TPE et PME du Rhône |
| Le bilan annuel d'Atlas Conseil | coûte | 1 200 € HT |
| Le bilan annuel d'Atlas Conseil | dure | trois semaines |
| Le régime de TVA d'une entreprise | dépend de | son chiffre d'affaires annuel |
| La liasse fiscale | accompagne | la déclaration de résultat |

**Les huit règles** (le détail et des réécritures avant/après :
`references/ecrire-en-triplets.md`) :

1. **Le sujet est nommé, jamais un pronom.** « Il coûte 1 200 € » n'est
   extractible que si le moteur a gardé la phrase d'avant. Il ne l'a pas
   gardée. Test : coupez la phrase seule ; dit-elle encore de quoi elle parle ?
2. **Un prédicat précis.** Un verbe d'état ou de relation : est, coûte, dure,
   comprend, s'applique à, exige, permet de, est situé à. Pas « joue un rôle
   clé dans », qui n'affirme rien.
3. **Un objet vérifiable.** Un chiffre avec son unité (1 200 € HT, 3
   semaines, 20 %), une date, une entité nommée.
4. **Une idée par phrase.** Deux faits sur le même sujet peuvent partager
   une phrase (« coûte 1 200 € HT et dure trois semaines ») ; trois faits,
   jamais.
5. **Près du haut.** Les 3 à 5 triplets clés de la page tiennent dans les
   200 premiers mots (la réponse directe), puis chaque section s'ouvre par
   son propre triplet. Le reste développe, prouve, nuance.
6. **La valeur canonique, copiée, jamais réécrite.** « 1 200 € HT » partout,
   pas « environ 1 200 € » ici et « 1 250 € » là. La valeur vient du registre.
7. **Le temps est explicite.** « En 2026, … », « Depuis le 1er janvier 2026,
   … ». Une ancienne valeur se signale (« Auparavant », « jusqu'en 2025 ») :
   le contrôle de cohérence la reconnaît et ne la compte pas comme une
   contradiction.
8. **Le jargon est défini à sa première occurrence**, dans le corps : « La
   liasse fiscale désigne l'ensemble des formulaires… », ou le sigle entre
   parenthèses après sa forme longue. Chaque terme défini devient un
   `DefinedTerm`. Pas de définition de dictionnaire en ouverture : le
   triplet d'ouverture répond à la question du lecteur.

## 2. Les entités — relier chaque nom à un identifiant stable

Un nom est ambigu ; un identifiant ne l'est pas. Chaque entité principale de
la page est reliée, dans le JSON-LD, à ce qui l'identifie sans équivoque.

| Où | Propriété | Règle |
|----|-----------|-------|
| `WebPage` | `about` | 1 à 3 entités : le sujet. Test : sans elle, la page est hors sujet |
| `WebPage` | `mentions` | 12 au plus, **visibles dans le contenu principal** |
| Chaque entité | `sameAs` | `https://www.wikidata.org/wiki/Q…`, l'article Wikipédia, le site officiel |
| Jargon | `DefinedTerm` | `name`, `description` (la définition du texte), `inDefinedTermSet` → le glossaire |
| `Organization` | `knowsAbout` | Les domaines d'expertise, en `Thing` avec `sameAs` — les mêmes que les `about` des pages de service |
| `Service` | `provider` | `{"@id": "…/#organization"}`, et `category` → le `Thing` désambiguïsé |
| `BlogPosting` | `author` | `{"@id": "…/#/schema/person/…"}` : une `Person` avec `knowsAbout`, `sameAs` (LinkedIn), `worksFor` |

Graphe complet et cas particuliers : `references/jsonld-entites.md`.

**Aucun QID de mémoire.** On le cherche, on lit la description, on
l'inscrit au registre ; puis on le réutilise partout. Une entité non
vérifiée part **sans `sameAs`** : un balisage incomplet se corrige, un faux
`sameAs` affirme une chose fausse avec aplomb.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/triplets.py" wikidata "Expertise comptable"
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/triplets.py" wikidata "Atlas Conseil" --site atlas-conseil.example
```

Avec `--site`, seul l'élément dont le site officiel (P856) est ce domaine
est marqué ✅ : un homonyme (une maison d'édition du même nom) n'est pas
votre entité. Sans réseau, le script le dit et on inscrit l'entité sans QID.

## 2 bis. L'entité du site elle-même — le trio sémantique

Avant les entités dont parle la page, il y a celles qui **parlent** :
l'organisation et ses auteurs. Un moteur cite quelqu'un quand trois couches
concordent : **qui est-ce** (l'entité), **comment le sait-il sans
ambiguïté** (les données structurées), **est-ce que tout ce qu'il lit
concorde** (le contenu, sur le site et ailleurs). Qu'une couche flanche, et
l'expert devient trois inconnus.

**La fiche d'identité, vérifiée — jamais devinée.** Raison sociale, forme,
numéro d'immatriculation, date de création, siège, dirigeant : relevés dans
le registre officiel des entreprises (en France, le RNE : outil infosociétés
`search_company` puis `get_company` s'il est branché, sinon
annuaire-entreprises.data.gouv.fr), avec la date du relevé. Les profils
(LinkedIn entreprise et personne, chaîne vidéo, newsletter, fiche
d'établissement) sont ouverts un par un : un profil qui ne répond pas n'entre
pas dans `sameAs`. Un fait qu'on ne peut pas sourcer ne va ni dans le
JSON-LD ni dans le texte. La fiche entre au registre (`entites.csv`).

**Une entité, un `@id`, partout.** `https://exemple.com/#organization` pour
l'organisation, un `@id` stable par personne (voir `seo-schema-jsonld`).
Chaque bloc qui parle d'elles **référence** cet `@id`
(`"author": {"@id": "…"}`) au lieu de les redécrire : sinon le moteur voit
une personne de plus. Signaux d'alerte, à relever sur 3-4 pages clés :
- une `Organization` sans `sameAs` ;
- plusieurs `@id` pour la même personne — typiquement l'empreinte générée
  par l'extension SEO (`#/schema/person/<empreinte>`) **et** un `@id` maison :
  fusionner dans un seul, côté serveur, sur toutes les pages ;
- des blocs `"@type": "Person"` sans `@id` ;
- deux URL différentes pour le même profil.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/schema_validate.py" https://exemple.com/ --socle socle-global.json
```

**La correction se fait côté serveur, une fois pour tout le site** : une
extension qui complète le graphe de l'extension SEO (données officielles,
`sameAs`, fondateur, fusion des personnes générées dans l'`@id` maison) :
sur WordPress, `templates/wordpress/plugins/seo-entite/`. Les générateurs
de pages du projet écrivent directement les `@id` stables. Jamais une
correction page par page dans le contenu : la page suivante oublierait.

**Vérifier après la correction**, sur le site en ligne et pas sur le
fichier :
1. sur 3-4 pages clés (accueil, une page de service, un article, la page
   d'entité) : **une seule** `Organization` et **une seule** `Person` par
   entité, plus aucune référence `#/schema/person/<empreinte>` restante,
   `sameAs` présents ;
2. le test des résultats enrichis de Google sur 2 ou 3 pages ; il demande
   un navigateur : à faire faire par une personne, résultat noté ;
3. l'état consigné dans la mémoire du projet (version de l'extension, date,
   pages vérifiées), pour que la prochaine session ne recommence pas
   l'audit.

**Une page d'entité par entité** (« entity home ») : la page qui décrit la
personne ou l'organisation — parcours vérifiable, profils, publications —
vers laquelle pointent les `sameAs`, les bylines et le bloc auteur. Faits
sourcés uniquement, validée par la personne avant publication.

**Hors du site** : fiche d'établissement, LinkedIn, annuaires
professionnels, Wikidata **seulement** si les critères de notoriété sont
remplis (un élément créé pour une entité non notable est supprimé). Même
nom, même adresse, même description courte partout — `geo-llms-txt` pour la
cohérence de marque, `seo-eeat` pour la page auteur.

## 3. Le registre — une valeur par sujet et prédicat

Deux fichiers du projet, dans `memoire/`, lus par le script et par chaque
skill qui écrit (format complet : `references/registre.md`) :

- **`entites.csv`** — `entite,type,qid,sameAs,definition,alias` : chaque
  entité vérifiée une fois, réutilisée partout. `sameAs` et `alias` acceptent
  plusieurs valeurs séparées par `|`.
- **`triplets.csv`** — `sujet,predicat,objet,source,date_verif,pages` : les
  faits canoniques du site, avec leur source et leur date. `pages` dit où le
  fait **doit** être affirmé (`*` = partout, sinon les slugs ou chemins
  séparés par `|`).

Une ligne qui commence par `#` est un commentaire. Chaque chiffre de
`memoire/faits.md` a sa ligne dans `triplets.csv`, **à l'identique** ;
`triplets.csv` y ajoute les faits non chiffrés (définition, localisation,
périmètre, public). Le jour où un fait change : on corrige le registre,
puis `coherence` liste les pages à reprendre.

## 4. Dans la chaîne de production

| Étape | Ce que les triplets y font |
|-------|----------------------------|
| **Brief** (`seo-brief`) | Section « Triplets à affirmer » : 3 à 8 lignes sujet — prédicat — objet, avec source et emplacement (intro, H2, FAQ), tirées de `triplets.csv` pour la page, plus les entités et leur QID |
| **Rédaction** (`seo-redaction`) | Un triplet = une phrase, sujet nommé. Les 2 ou 3 principaux dans la réponse directe ; chaque H2 s'ouvre par le sien |
| **FAQ** (`seo-faq-paa`) | Chaque réponse commence par le triplet qui répond : « Combien coûte le bilan annuel ? » → « Le bilan annuel d'Atlas Conseil coûte 1 200 € HT. » |
| **JSON-LD** (`seo-schema-jsonld`) | `triplets.py jsonld` produit `about`/`mentions` ; un prix balisé (`Offer`) égale la valeur du triplet |
| **llms.txt** (`geo-llms-txt`) | La ligne de chaque page clé est son triplet principal ; une section « Faits clés » reprend les triplets de la marque, mot pour mot |
| **Hors site** | Mêmes triplets sur la fiche Google, LinkedIn, les annuaires, les déclarations Wikidata (site officiel, date de création, siège) : les modèles recoupent |

Gabarits prêts à copier (brief, FAQ, llms.txt) : `references/ecrire-en-triplets.md`.

## 5. Vérifier — le script

```bash
# Ce que la page affirme : triplets candidats, entités du JSON-LD, sujets implicites en tête
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/triplets.py" extraire <page.html|url|fichier.md> [--tout] [--json]

# La page face au registre : triplets requis, entités sans sameAs, saillance, couverture
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/triplets.py" verifier <page> --page /offres/bilan-annuel/ [--strict] [--seuil 100]

# Le site : même sujet + prédicat, valeurs différentes
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/triplets.py" coherence contenus/ --triplets memoire/triplets.csv [--textes] [--strict]
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/triplets.py" coherence --urls crawl.csv --max 200

# Le fragment à fusionner dans le graphe de la page
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/triplets.py" jsonld --about "Bilan comptable" --depuis page.html \
  --url https://www.atlas-conseil.example/offres/bilan-annuel/ [--glossaire …/glossaire/#termes]
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/triplets.py" jsonld --organisation   # knowsAbout de l'Organization
```

| Statut d'un triplet requis | Sens | Correction |
|----------------------------|------|------------|
| **affirmé** | Une phrase porte le sujet et la valeur | — (vérifier qu'elle est en tête si c'est un fait clé) |
| **implicite** | La valeur est là, mais le sujet est un pronom (« Elle dure 3 semaines ») | Renommer le sujet dans la phrase |
| **contredit** | Le sujet est là avec une autre valeur de même unité, ou un autre objet pour un prédicat à valeur unique (est situé à, coûte, dure, désigne…) | Remettre la valeur du registre |
| **absent** | Le fait n'est pas dit | L'écrire, en triplet, à l'endroit prévu par le brief |

`verifier --strict` renvoie 1 s'il y a une contradiction, un QID différent
du registre ou une couverture sous `--seuil` : c'est le contrôle qui bloque
une livraison. `coherence --strict` renvoie 1 à la première contradiction.

Le contrôle de cohérence lit les pages HTML (contenu principal seulement :
ni menu ni pied de page), Markdown et JSON (chaque chaîne de texte d'un
fichier de contenu), ou une liste d'URL. Il ne compare pas les sujets trop
généraux (« le prix », « le délai ») ni les prédicats à plusieurs valeurs
(« propose », « comprend ») : deux offres différentes ont deux prix.

## 6. La saillance — la page parle-t-elle de ce qu'elle déclare ?

La saillance, c'est le poids d'une entité dans un texte. Un modèle
d'entités l'évalue à partir de la position (titre, H1, début de texte), de
la fréquence et du rôle grammatical (sujet plutôt que complément). Si
l'entité de `about` n'est pas la plus saillante, la page parle d'autre
chose que ce qu'elle déclare.

`verifier` en donne une mesure heuristique (H1 : 3, title : 2, 100
premiers mots : 2, un intertitre : 1, occurrences : 0,5 chacune, plafonnées)
et signale :

- une entité `about` au-delà du 3e rang et sous la moitié du score du plus
  saillant → la nommer dans le H1, le title ou l'introduction, en sujet ;
- l'entité la plus saillante absente de `about` → soit elle est le vrai
  sujet (corriger `about`), soit la page dérive (recentrer le texte).

Pour une mesure externe, l'API Natural Language de Google (`analyzeEntities`)
renvoie un score de saillance par entité ; elle demande une clé, le script
ne l'appelle pas. Le test qui compte reste celui des moteurs : posez-leur
les questions dont les triplets sont la réponse (« Combien coûte un bilan
annuel chez Atlas Conseil ? ») et comparez (`geo-share-of-model`).

## 7. Mode automatique — dans les routines

Appelé par `seo-cycle` (modes contenu et optimisation) ou par une routine,
le skill applique ceci, sans poser de question, dans les limites des
niveaux d'autonomie de `CLAUDE.md` :

1. **Avant de publier une page créée ou modifiée** :
   `triplets.py verifier <page> --strict`. Triplet absent, implicite ou
   contredit → réécrire la phrase (sujet nommé, valeur du registre). Entité
   sans `sameAs` ou absente du JSON-LD → `triplets.py jsonld` et fusion
   dans le graphe, puis `schema_validate.py --strict`.
2. **Chaque semaine** : `triplets.py coherence contenus/ --triplets
   memoire/triplets.csv --json` (ou `--urls` sur un site en CMS). Un **écart
   au registre** : la page a tort, on la corrige. Une **contradiction entre
   pages sans valeur au registre** : l'agent ne choisit jamais ; il inscrit
   le tableau dans `rapports/a-valider.md` avec les sources à consulter.
3. **Nouvelle entité rencontrée** : `triplets.py wikidata "<libellé>"`
   (`--site` pour une organisation). QID inscrit seulement s'il y a un seul
   candidat dont la description correspond au sens de la page (et, pour une
   organisation, dont P856 est son domaine). Sinon : inscrite sans QID,
   ligne dans `rapports/a-valider.md`. Un QID existant ne se remplace que
   si Wikidata le signale fusionné.
4. **Nouveau triplet au registre** : seulement avec une source officielle
   lue dans la session et la date du jour dans `date_verif`. Jamais une
   valeur modifiée sans source.
5. **Journal** : chaque correction publiée passe par `seo-journal-mesure` ;
   le run note la couverture par page et le nombre de contradictions.

| Action | Niveau |
|--------|--------|
| JSON-LD `about`/`mentions`/`sameAs`, `DefinedTerm`, `knowsAbout` | Automatique (c'est du schema) |
| Phrase réécrite sur une page neuve (brouillon) | Automatique |
| Phrase réécrite sur une page qui ranke | Validation |
| Choisir entre deux valeurs contradictoires sans registre | Jamais seul |
| QID inscrit au registre | Automatique si candidat unique et vérifié, sinon validation |

## Livrables

- `memoire/entites.csv` et `memoire/triplets.csv` — le registre, à jour
- Dans le brief : la section « Triplets à affirmer »
- Le fragment JSON-LD `about`/`mentions` de chaque page, fusionné dans son graphe
- `COHERENCE-FAITS.md` — le tableau de `coherence`, avec pour chaque ligne la
  valeur retenue, sa source et les pages corrigées
- Le résultat de `verifier` pour chaque page livrée
