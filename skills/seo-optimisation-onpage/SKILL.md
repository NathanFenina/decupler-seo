---
name: seo-optimisation-onpage
description: >
  Audite une page existante face à un mot-clé (score /100, feux par critère,
  couverture des entités, Search Console, maillage entrant) puis livre la
  version optimisée complète, prête à coller. Remplace Yoast et Rank Math.
  Déclencher sur « optimise cette page », « score SEO », « audit on-page », «
  passe au vert », « combien de fois répéter le mot-clé », ou une URL ou un
  texte avec un mot-clé. Pas pour une page neuve → seo-brief puis
  seo-redaction.
---

# Optimisation on-page — noter puis corriger

Les plugins SEO vous disent que c'est orange. Ils ne le passent pas au vert.
Ce skill fait les deux.



**Sans projet configuré, sans données ni accès** (dossier vide, pas de
Search Console, pas d'outil web) : ne vous arrêtez pas sur une question.
Livrez tout de suite ce qui ne dépend pas des données — la méthode appliquée
au cas, un exemple rempli, le livrable type avec des emplacements
`[à compléter : …]` — puis, en fin de réponse, la liste de ce qu'il faut
fournir pour la version chiffrée. Aucun chiffre inventé.

## L'essentiel — ce qui ne se négocie pas

1. **Mot-clé sans quota** : title, H1, première phrase ; la pertinence se juge sur la **couverture des entités**, jamais sur une densité.
2. **Search Console d'abord** sur une page existante : requêtes réelles et cannibalisation avant toute réécriture.
3. **Livrer la page entière** prête à coller (jamais « conserver l'existant »), liens internes déjà insérés.
4. **Zéro information non vérifiée** présentée comme vraie : source ou « à valider ».
5. **Garder ce qui marche** : une page qui ranke s'enrichit, elle ne se réécrit pas de zéro.

## Entrées

- Le contenu : URL (à récupérer) ou texte collé
- Le mot-clé cible principal — **s'il n'est pas donné, demandez-le.** Sans
  cible, il n'y a pas d'optimisation possible. Si personne ne peut répondre
  (routine, lot de pages), déduisez-le du title, du H1 et de l'URL,
  **annoncez-le** en tête du rapport (« audité sur : … — à corriger si
  l'extension SEO visait autre chose ») et marquez le score « sous réserve ».
  Pour comparer avec le score de Yoast ou Rank Math, il faut **le même**
  mot-clé que le leur : sinon on compare deux cibles.
- Les secondaires, si connus
- La liste des pages du site (carte de contenu `wp.py carte`, sitemap) :
  c'est elle qui permet de poser de vrais liens internes à la réécriture.
  Sans elle, l'emplacement est marqué `[lien interne : sujet]`, jamais une
  URL devinée
- Le type de livrable : **OPTIMISATION** (page existante) ou **CRÉATION**
  (page neuve), et le format (texte à coller ou Word)

## La méthode : optimiser par entités, pas par mot-clé exact

Google comprend un sujet par ses **entités** (Knowledge Graph) et leurs
relations, pas par la répétition d'une chaîne de caractères. La densité
n'est pas un facteur de classement, et la répétition forcée relève du
bourrage (politiques anti-spam de Google). Le mot-clé garde un rôle
**d'alignement** sur les emplacements forts — la correspondance du title
compte toujours — mais plus aucun rôle de volume.

**1. La carte des entités, avant toute rédaction**

| Niveau | Quoi | Sources |
|---|---|---|
| Entité principale | Le concept que la page doit « posséder » | mot-clé, intention de recherche |
| Entités très liées (3-6) | Ce sans quoi le sujet n'est pas traité : processus, étapes, documents, indicateurs, composants | SERP top 10, Wikidata, PAA, Search Console |
| Entités de contexte (5-12) | Produits, marques, normes, métiers, lieux, organismes | offre du client, SERP, Search Console |
| Attributs et relations | Ce que les concurrents disent de l'entité : définition, étapes, coûts, durée, critères de choix, limites | H2/H3 récurrents du top 10, PAA |

Lacunes prioritaires = entités et attributs présents chez **au moins 3
concurrents du top 10** et absents de la page (`serp_concurrents.py`,
skill `seo-serp-analysis`).

**2. Les règles de rédaction**

- **Mot-clé exact aux seuls emplacements forts** : title, H1, première
  phrase (la définition), éventuellement **un** H2 et **une** question de
  FAQ si c'est naturel. **Aucun nombre d'occurrences à viser** : ce sont
  des emplacements, pas un compte. Ne jamais tordre une phrase pour placer
  l'expression exacte.
- **Chaque entité très liée** est nommée, expliquée et reliée à l'entité
  principale (« X automatise Y entre A, B et C »).
- **Relations explicites** sujet → verbe → objet : « X permet de… »,
  « X se compose de… », « X s'intègre à… » (skill `seo-entites-triplets`).
- **Variantes, synonymes et champ lexical** partout ailleurs.
- **Désambiguïser** : le nom complet à la première mention (éditeur +
  produit + version, organisme en toutes lettres).
- **Profondeur plutôt que répétition** : une entité bien expliquée vaut
  mieux que trois mentions vides.
- **Cohérence avec le JSON-LD** : entité principale (+ 1-2 très liées) en
  `about`, entités de contexte réellement citées en `mentions`.

**Exigence d'un client.** Si un client impose un nombre d'occurrences
(`regles.mot_cle_occurrences_min` dans `decupler-seo.config.yml`), on le
respecte, en le contrôlant hors score (`--occurrences-min`), sans jamais
dépasser le plafond de densité (`regles.densite_max_pct`). Vide = méthode
par entités, aucun quota.

## Les règles GEO qui tiennent en 2026

Pour Google, le GEO **est** du SEO : les réponses IA s'appuient sur le
classement habituel et éclatent la question en sous-requêtes (*fan-out*).
Sources et niveaux de preuve de chaque règle : `references/preuves-2026.md`.

1. **Accès d'abord** : page indexable, pas de `nosnippet` involontaire ;
   robots.txt et CDN qui laissent passer Googlebot, Bingbot, OAI-SearchBot,
   Claude-SearchBot et PerplexityBot (`agents_ia.py`) ; contenu principal
   dans le **HTML initial**, rien d'essentiel dans un onglet, un PDF ou une
   image.
2. **Couvrir le fan-out dans la page** : la requête et ses 8 à 15
   sous-questions (suite logique, généralisation, précision, comparaison,
   implication…), **une section H2/H3 par sous-question**. Jamais une page
   par variante : c'est de l'abus de contenu à grande échelle.
3. **L'essentiel dans le premier tiers** : réponse directe de 40 à 60 mots
   sous le H1, définition de l'entité dans l'introduction, résumé des points
   clés — c'est là que se prennent près de la moitié des citations.
4. **Des passages citables** : sections d'environ 120 à 180 mots, chacune
   ouverte par 1 à 2 phrases autonomes (6 à 20 mots) qui répondent hors
   contexte ; l'entité nommée plutôt que « il » ; une idée par phrase. Ne
   pas micro-découper pour autant (Google le déconseille).
5. **Apport d'information** : au moins **3 éléments absents du top 10 et de
   la réponse qu'un LLM donnerait seul** — donnée propre, test de première
   main, cas chiffré, expert interne, photo originale, grille de décision.
   Le contrôle : générer la réponse d'un assistant sur la requête et lister
   ce que la page apporte en plus.
6. **Des preuves** : au moins une donnée sourcée par section clé, 1 à 2
   citations d'experts nommés avec leur fonction. Zéro chiffre inventé.
7. **Title en langage naturel**, proche de la requête principale (50-60
   caractères, entité dans les 40 premiers), sans répétition du mot-clé ;
   slug lisible de 4 à 7 mots ; title, H1 et meta alignés.
8. **Dates honnêtes** : « Publié / Mis à jour le » visible et identique au
   JSON-LD ; une date ne change qu'avec un changement réel du contenu.
9. **Ne pas faire** : llms.txt « pour le SEO », schema « pour l'IA »,
   campagnes de mentions artificielles, date rafraîchie sans changement.

## Mesurer

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/onpage_score.py" <url|fichier.html> "mot-clé" \
  --entites "entité liée 1, entité liée 2, …" \
  [--secondaires "variante 1, variante 2"] [--url https://…/slug/] [--na "FAQ,Fraîcheur"] \
  [--occurrences-min 20] [--json]
```

`--entites` reçoit la carte des entités (très liées + contexte) : le
script dit où chacune apparaît (intertitre, texte) ou qu'elle manque.
Sans elle, la couverture n'est qu'une richesse lexicale approximative.

Le script mesure ; vous interprétez, vous vérifiez les heuristiques
(voix passive, entités vagues) à la lecture, et vous réécrivez.
`--url` sert au test du slug quand le fichier n'a pas de canonical ;
`--na` déclare les critères sans objet pour ce type de page.

## Les règles de notation

| Feu | Points | Quand |
|-----|--------|-------|
| 🟢 | 100 % du critère | Le seuil vert est atteint |
| 🟡 | 50 %, arrondi au supérieur | Entre les deux |
| 🔴 | 0 | Optimisation ratée ou absente |
| ⚪ | retiré | **Non applicable** : ses points sont redistribués au prorata dans sa catégorie, et le score est annoncé « sous réserve » |

- **Information non fournie ≠ 🔴.** Un texte collé sans title ni meta :
  ces critères sont ⚪, pas rouges. Une meta présente et trop longue : 🔴.
- **Dans le doute, le feu le plus sévère.** Un audit indulgent ne sert à rien.
- **Chaque critère porte une phrase « Pourquoi ça compte »** — l'effet
  concret, pas la règle. Le script la fournit ; reformulez-la pour le client.

**Malus de sur-optimisation**, appliqué au score global et affiché
explicitement (« 83, −8 → 75 ») :

| Densité effective | Malus |
|-------------------|-------|
| ≤ 3,5 % | 0 |
| 3,5 – 5 % | −5 |
| 5 – 6,5 % | −8 |
| > 6,5 % | −12 |

**Densité effective = max(densité exacte, densité distribuée).** La
correspondance distribuée retire les mots vides du mot-clé (« prix d'une
pompe à chaleur » → prix, pompe, chaleur) et compte chaque fenêtre de
(mots utiles + 4) mots qui les contient tous. Pourquoi : le bourrage
déguisé en variantes reste du bourrage, et Google le lit comme tel.

**Bandes** : 80-100 🟢 publiable · 55-79 🟡 à retravailler · 0-54 🔴 à réécrire.

## Le barème — 100 points

### A · Balises et structure (20)

| Critère | Pts | 🟢 | 🟡 | 🔴 |
|---------|-----|----|----|----|
| Title | 5 | Mot-clé (ou tous ses mots utiles) dans les premiers mots, 50-60 car. | Présent mais tardif, variante, ou hors 50-60 | Absent, ou sans mot-clé |
| Title accrocheur | 1 | Un chiffre ou un mot fort (guide, prix, comparatif…) | Ni l'un ni l'autre | — |
| Longueur de la meta | 2 | **120-156 car.** | 100-119 ou 157-170 | Absente, < 100 ou > 170 |
| Mot-clé dans la meta | 2 | Présent | Variante | Absent |
| H1 | 4 | Unique, contient le mot-clé | Variante, ou plusieurs H1 avec mot-clé | Absent, ou sans mot-clé |
| Hiérarchie Hn | 3 | Séquentielle, ≥ 3 titres | Un saut de niveau, ou < 3 titres | Plusieurs sauts, ou aucun titre |
| Mot-clé dans le slug | 3 | **Tous** les mots utiles | Une partie | Aucun |

> Harmonisation : la zone verte de la meta est **120-156 caractères**
> partout (script, barème, livrables). L'ancien 150-160 excluait des metas
> courtes et complètes, et laissait passer des metas tronquées sur mobile.

### B · Contenu et sémantique (25)

| Critère | Pts | 🟢 | 🟡 | 🔴 |
|---------|-----|----|----|----|
| Alignement du mot-clé | 5 | H1 + ouverture (100 premiers mots) ; un H2 en plus si naturel | L'un des deux | Ni l'un ni l'autre |
| Pas de sur-optimisation | 3 | Densité effective ≤ 2,5 % — **aucun minimum** | 2,5 – 3,5 % | > 3,5 % |
| Mot-clé dans un alt | 2 | ≥ 1 alt avec le mot-clé | Variante | Aucun (⚪ sans image) |
| Mots-clés secondaires | 3 | Tous présents, aucun > 2,5 % | La moitié, aucun > 3,5 % | Moins, ou bourrés (⚪ si non fournis) |
| Couverture des entités | 4 | ≥ 80 % de la carte des entités présente | ≥ 50 % | Moins |
| Profondeur | 4 | Au niveau du top 3 | En dessous | Contenu mince |
| Originalité et preuves | 2 | Données, exemples, méthode propres | Un élément | Paraphrase |
| Clarté des entités | 2 | Chaque passage nomme ce dont il parle | 1-2 « notre solution », « la ville » | Récurrent |

### C · Lisibilité (15)

| Critère | Pts | 🟢 | 🟡 | 🔴 |
|---------|-----|----|----|----|
| Fréquence des intertitres | 3 | 1 H2/H3 pour ~300 mots | Plus espacés | Un bloc > 500 mots sans titre |
| Phrases de plus de 20 mots | 3 | < 25 % | 25 – 35 % | > 35 % |
| Paragraphes | 3 | ≤ 150 mots | Un > 150 | Plusieurs > 200 |
| Mots de transition | 3 | ≥ 30 % des phrases | 20 – 30 % | < 20 % |
| Voix passive | 3 | < 10 % | 10 – 20 % | > 20 % |

### D · GEO et citabilité (15)

| Critère | Pts | 🟢 | 🔴 |
|---------|-----|----|----|
| Réponse directe | 5 | 40-60 mots en haut, autonome | Aucune réponse avant le 3e écran |
| Structure extractible | 3 | Listes, tableaux, titres explicites | Bloc de texte continu |
| Définitions | 2 | Termes clés définis en une phrase autonome | Rien de définissable |
| FAQ | 3 | 4-6 questions (8-12 sur un pilier), réponses de 40-80 mots dont la première phrase répond | Absente |
| Données sourcées | 2 | Chiffres avec source vérifiable | Chiffres non sourcés, ou aucun |

### E · E-E-A-T (15)

| Critère | Pts | 🟢 | 🔴 |
|---------|-----|----|----|
| Auteur identifié avec credentials | 4 | Signature + page auteur | Aucune |
| Expérience de première main | 4 | Cas, chiffres, constats propres | Généralités |
| Sources externes d'autorité | 2 | ≥ 3 | Aucune |
| Fraîcheur | 3 | Mise à jour datée < 12 mois (🟡 au-delà) | Aucune date |
| Transparence | 2 | Contact, mentions, affiliations déclarées | Rien |

### F · Maillage et technique (10)

| Critère | Pts | 🟢 | 🔴 |
|---------|-----|----|----|
| Liens internes contextuels | 3 | ≥ 3 | Aucun |
| Ancres descriptives | 2 | Aucune ancre générique | > 20 % de « cliquez ici », « en savoir plus » |
| Liens externes | 1 | ≥ 1 pertinent | Aucun |
| Images avec alt | 2 | Toutes | Aucune image ou aucun alt |
| Schema JSON-LD | 2 | Adapté et valide (`seo-schema-jsonld`) | Absent |

## Search Console — obligatoire en optimisation

Fenêtres : **3 derniers mois** (données finales) et les **3 mois
précédents** pour la tendance (`gsc.py`, skill `seo-gsc-analyses`).

1. **Requêtes de la page** : clics, impressions, CTR, position. Elles
   donnent les secondaires réelles, les **opportunités** (position 5-20
   avec impressions, CTR faible) et des entités exprimées par les
   internautes, à ajouter à la carte.
2. **Cannibalisation** (requête × page, tout le site, sur le mot-clé et
   les principales requêtes de la page) : quelles autres URL prennent des
   impressions sur les mêmes requêtes ?
3. **Verdict par requête partagée** : *pas de risque* (intentions
   différentes, l'autre URL très loin) · *à surveiller* · *cannibalisation*
   (deux URL alternent ou se partagent clics et positions).
4. **Action** : différencier l'angle et les entités de chaque page,
   réserver l'ancre exacte à la page cible et la retirer des liens vers
   l'URL concurrente, consolider (fusion + 301) ou canonical en dernier
   recours.

## Maillage interne entrant

Les liens sortants ne suffisent pas : une page se renforce surtout par les
liens qu'elle **reçoit**.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/crawl_site.py" https://exemple.com --liens liens.csv --exporter crawl.csv
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gsc.py" perf --par page --jours 90 --lignes 5000 --json > gsc-pages.json
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/maillage_entrant.py" --liens liens.csv --pages crawl.csv \
  --cible <url> --mot-cle "<mot-clé>" --entites "<entités liées>" --gsc gsc-pages.json --marque "<marque>"
```

1. **Existant** : page source, ancre, zone (contenu, menu, en-tête, pied
   de page, fil d'Ariane), statut (OK, ancre générique, hors contenu), et
   diversité des ancres en contenu (exacte, partielle, marque, générique).
2. **Ancres concurrentes** : le mot-clé de la page utilisé comme ancre
   vers une autre URL — cannibalisation par le maillage, à corriger.
3. **Opportunités dosées**, pas une longue liste : page cible faible → 4-5
   liens, moyenne → 2-3, forte → 1-2 (ou seulement corriger les ancres).
   Sources = pages puissantes (clics + impressions sur 3 mois, PageRank
   interne des liens de contenu) ou très proches du sujet, qui ne lient
   pas déjà la cible. **Ancre exacte une seule fois**, sur la meilleure
   source ; ailleurs, ancres partielles ou par entité liée, jamais deux
   fois la même. Pour chacune : la phrase existante où poser le lien, ou
   la phrase à ajouter, écrite.

## Ajouter une information : la vérifier d'abord

Ajouter ce qui manque (fonctionnalités, réglementation, chiffres de
marché, nouveautés) est encouragé, à condition de le vérifier :

1. **Produit, outil, partenaire** : ne le présenter comme une offre du
   client que si son site le montre (page dédiée, cas client). Sinon,
   exemple du marché, signalé « à valider ».
2. **Réglementation et dates** : la source officielle, jamais de mémoire.
3. **Fonctionnalités d'un logiciel** : la documentation de l'éditeur ;
   décrire exactement ce que fait l'outil.
4. **Le contenu existant** passe la même vérification : une affirmation
   fausse est corrigée et signalée dans l'audit.
5. **Traçabilité** : chaque ajout listé avec sa source ; ce qui n'a pas
   pu être confirmé est marqué « à valider avec le client ». Rien de non
   vérifié n'est présenté comme vérifié.

## Auteur

Une ligne visible : « Rédigé par <expert>, <fonction> chez <marque> —
mis à jour en <mois année> », et `author` + `dateModified` dans le
JSON-LD. **Pas de « relu par » ni de `reviewedBy`** sans relecture
réellement confirmée par le client.

## Le rapport

```
SCORE : 83, −8 → 75/100  🟡   (sous réserve : FAQ ⚪)

  A · Balises et structure    18/20  🟢
  B · Contenu et sémantique   18/25  🟡
  C · Lisibilité              12/15  🟢
  D · GEO et citabilité       11/15  🟡
  E · E-E-A-T                 14/15  🟢
  F · Maillage et technique   10/10  🟢
  Malus : densité effective 5,4 % → −8
```

Puis, pour chaque critère non vert, du rouge au jaune :

1. **Ce qui est en place** — la valeur actuelle, citée
2. **Pourquoi ça compte** — une phrase, l'effet concret
3. **Le correctif** — la version corrigée, écrite

> **Title — 3/5 🟡**
> Actuel : « Nos prestations de plomberie » (29 car.)
> Pourquoi ça compte : c'est la ligne cliquable de la SERP ; sans lieu ni
> promesse, elle ne donne aucune raison de cliquer plutôt que sur les neuf
> autres.
> **Corrigé** : « Plombier à Lyon : dépannage en 2 h, devis gratuit » (52 car.)

## Les livrables

### OPTIMISATION — cinq parties (onglets d'un document, ou sections)

**① Audit** — score et feux, **carte et couverture des entités**,
alignement du mot-clé, **Search Console (requêtes et cannibalisation)**,
plan Hn actuel → recommandé (CONSERVER / MODIFIER / NOUVEAU), E-E-A-T,
GEO, liens sortants à créer, ajouts vérifiés et « à valider », plan
d'action priorisé. Toutes les sections remplies, pas une synthèse.

**② Optimisations en couleur** — pour le relecteur :
- **vert** = ajouté ; **noir** = conservé ; *gris italique* = consigne à
  l'intégrateur (où placer l'image, quel bloc déplacer)
- chaque bloc nouveau est **écrit en entier**, jamais un renvoi
  (« ajouter une section sur les aides » n'est pas un livrable)

**③ Contenu optimisé « à coller »** — tout en noir, pour l'intégrateur :
- Title et Meta en premier
- chaque titre balisé en tête de ligne : `H1 :`, `H2 :`, `H3 :`
- **le contenu ENTIER** : jamais « [conserver l'existant] », volume ≥
  l'original
- liens internes **déjà insérés** dans le texte, avec leurs ancres
- **toutes les entités de la carte couvertes** ; mot-clé exact aux seuls
  emplacements forts

**④ Données structurées** — le `@graph` complet (skill `seo-schema-jsonld`) :
`about` et `mentions` alignés sur la carte des entités, `FAQPage` = la FAQ
de ③ mot pour mot, `author`, `datePublished`, `dateModified`.

**⑤ Maillage entrant** — liens existants et leurs ancres, ancres
concurrentes, opportunités dosées avec leur phrase (`maillage_entrant.py`).

### CRÉATION — deux parties

1. **Le brief** — intention, **carte des entités**, plan Hn, prompts GEO
   visés, FAQ, E-E-A-T, liens, schema, et requêtes déjà captées par des pages
   existantes (risque de cannibalisation) — voir `seo-brief`
2. **Le contenu à publier** — au format ③

### Variante Word avec suivi des modifications

Utilisez le skill docx s'il est disponible.

- Légende en tête : **vert** = ajouté, ~~rouge barré~~ = supprimé
- Hn **avant → après**
- Tableau des alt (image, alt actuel, alt proposé)
- JSON-LD `FAQPage` en fin de document
- Liens internes en deux tableaux : **« déjà intégré »** et **« à ajouter »**,
  chaque lien marqué `(lien interne)` dans le texte
- Récapitulatif des changements
- **Vérifier le rendu en PDF avant l'envoi** : un suivi de modifications
  illisible ne sera pas relu

### Ré-optimisation

Terminez toujours par :
- le tableau **« changement → critère passé au vert »**
- le score **avant → après**, avec le même barème (61 → 86)

## Pièges d'audit

- **Les erreurs de fond d'abord** : un intertitre copié d'une autre page du
  site, une section hors sujet, un chiffre qui contredit `memoire/faits.md`
  passent avant toute question de balise.
- **La sur-optimisation par le gabarit** : hero, intertitres de section,
  FAQ et bande CTA répètent souvent déjà le mot-clé. Mesurez sur le HTML
  **réellement servi** (URL), pas seulement sur le texte source, et
  corrigez par des variantes, jamais en supprimant des sections. Si
  l'audit ne porte que sur le texte collé, dites-le.
- **Quelle page possède quelle requête** : un article (actualité, retour
  d'événement, cas client) ne vise jamais la requête « entité + service »
  de la page qui convertit ; il vise sa longue traîne et renvoie vers elle
  avec cette ancre. Si Search Console montre l'article à sa place,
  recentrez l'article et renforcez le lien.

## Variante « audit seul »

Pour un client qui publie lui-même et ne veut pas de réécriture du corps :
recommandations ciblées — title, meta, H1, deux à quatre H2, introduction,
FAQ à ajouter, entités manquantes, liens — chacune écrite, prête à
appliquer. Même barème, même score avant → après estimé.

## La réécriture — les contraintes

- **Garder ce qui marche.** Ne réécrivez pas une page qui ranke déjà : vous
  remettriez le compteur à zéro. Ajoutez, précisez, restructurez.
- Ne jamais supprimer une information juste pour raccourcir
- Aucun chiffre inventé — si le texte d'origine cite un chiffre sans
  source, signalez-le plutôt que de le reprendre à votre compte
- Nommer les entités : le produit, la ville, l'organisation, pas « notre
  solution » ni « la ville »
- Respecter le ton du site (`config` → `projet.ton`)
- Le style humain : voir `seo-redaction`, section « ne pas écrire comme une IA »
- Contrôle final avant livraison : `controle_contenu.py` (voir `seo-redaction`)

## Livrables

- `ONPAGE-<slug>.md` — les cinq parties : audit, optimisations en couleur,
  « à coller », JSON-LD, maillage entrant
- `ONPAGE-<slug>.docx` — variante Word avec suivi des modifications
- `optimise-<slug>.html` — version HTML si destinée à un CMS (`seo-page-builder-html`)
- Le tableau avant/après par critère
