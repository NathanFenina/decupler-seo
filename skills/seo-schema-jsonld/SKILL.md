---
name: seo-schema-jsonld
description: >
  Définit, génère, valide et déploie le JSON-LD d'un site : un @graph par
  page, socle Organization + WebSite identique partout, nœuds par type de
  page, identité de l'organisation, pièges et dépréciations Google, contrôle
  par schema_validate.py. Déclencher sur « schema », « données structurées »,
  « JSON-LD », « rich results », « @graph », « vérifie mon JSON-LD ». Pour les
  seuls faits et entités → seo-entites-triplets.
---

# Données structurées — dire aux machines ce qu'est la page

Le schema ne fait pas ranker. Il fait **comprendre**, et il débloque des
affichages enrichis. En 2026, il a une seconde fonction, plus importante :
il dit aux moteurs IA qui est l'entité, ce qu'elle fait, et de quoi parle
chaque page — sans ambiguïté possible.



**Sans projet configuré, sans données ni accès** (dossier vide, pas de
Search Console, pas d'outil web) : ne vous arrêtez pas sur une question.
Livrez tout de suite ce qui ne dépend pas des données — la méthode appliquée
au cas, un exemple rempli, le livrable type avec des emplacements
`[à compléter : …]` — puis, en fin de réponse, la liste de ce qu'il faut
fournir pour la version chiffrée. Aucun chiffre inventé.

## L'essentiel — ce qui ne se négocie pas

1. **Un seul `@graph` par page**, socle Organization + WebSite identique partout.
2. **Tout fait balisé est visible** dans la page ; jamais de note sur sa propre organisation.
3. **Logiciel cité = `Thing`**, jamais `SoftwareApplication` hors sujet principal.
4. **Générer** (`schema_build.py`), **valider** (`schema_validate.py --strict`), jamais retoucher le JSON à la main.
5. **QID depuis le registre**, jamais de mémoire.
6. **Sans pouvoir lancer le script** (JSON collé, pas de shell) : appliquez à la main **chaque ligne** du tableau « Valider », hôte canonique compris, et livrez le graphe corrigé complet.

## L'architecture — deux couches, un seul graphe

**Un seul `<script type="application/ld+json">` par page, avec un seul
`@graph`.** Deux blocs qui décrivent chacun une `Organization` créent deux
entités concurrentes ; Google résout l'ambiguïté en ignorant les deux.

| Couche | Contenu | Règle |
|--------|---------|-------|
| **Socle global** | `Organization` (+ `#logo`) et `WebSite` | **Identique à l'octet près sur toutes les URL.** Généré depuis un seul fichier source (`socle-source.json` → `socle-global.json`), jamais retouché page par page |
| **Nœuds de page** | `WebPage` (ou sous-type), `Service`, `BreadcrumbList`, `BlogPosting`, `FAQPage`, `Person`… | Propres à l'URL, selon la matrice ci-dessous |

Pourquoi un fichier source : le jour où le téléphone ou le logo change, on
régénère le socle une fois, et toutes les pages restent cohérentes. Un
socle édité à la main diverge en trois mois.

**Si un plugin SEO produit déjà un graphe**, on n'en ajoute pas un second :
on injecte nos nœuds dans le sien, côté serveur.

- WordPress + Yoast : filtre `wpseo_schema_graph`
- WordPress + Rank Math : filtre `rank_math/json_ld`
- Les nœuds `Organization`/`WebSite` du plugin sont remplacés par ceux du
  socle (même `@id`), pas doublés

**Jamais via Google Tag Manager.** Un balisage injecté en JavaScript n'est
pas dans le HTML initial : les moteurs IA qui ne rendent pas le JavaScript
ne le voient pas, et Google le traite en différé. Rendu serveur, toujours.

Code d'injection et génération du socle : `references/deploiement.md`.

## Les @id — une entité, un identifiant, partout

| Nœud | @id |
|------|-----|
| Organisation | `{site}/#organization` |
| Logo | `{site}/#logo` |
| Site | `{site}/#website` |
| Page | `{canonical}#webpage` |
| Fil d'Ariane | `{canonical}#breadcrumb` |
| Service | `{canonical}#service` |
| Article | `{canonical}#article` |
| FAQ | `{canonical}#faq` |
| Personne | `{site}/#/schema/person/{slug}` — **le même sur toutes les pages** |

Toute relation passe par une référence `{"@id": "…"}`. Jamais un objet
recopié en ligne : un `publisher` réécrit dans l'article est une deuxième
`Organization`, avec ses propres fautes de frappe. Toute référence doit
pointer vers un nœud présent **dans le graphe de la page** — Google ne va
pas le chercher ailleurs.

## Matrice type de page → schemas

| Page | Nœuds de page (en plus du socle) |
|------|----------------------------------|
| Accueil | `WebPage` avec `about` → `#organization` |
| Service / page locale | `WebPage` + `Service` (mainEntity) + `BreadcrumbList` (+ `FAQPage`, `Person`) |
| Article | `WebPage` + `BlogPosting` (`author` → `Person`) + `BreadcrumbList` |
| Formation | `WebPage` + `Course` — prix dans `offers` **seulement s'il est affiché** |
| Liste / hub | `CollectionPage` + `ItemList` en `mainEntity` + `BreadcrumbList` |
| Contact / À propos / Auteur | `ContactPage` / `AboutPage` / `ProfilePage` + `Person` ou `#organization` en `mainEntity` |

**La FAQ est un nœud séparé** (`FAQPage`, `@id` `#faq`), relié à la page
par `hasPart` / `isPartOf`. Posée comme `mainEntity`, elle écraserait le
vrai sujet de la page (le service, l'article).

```json
{
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "Organization", "@id": "https://exemple.com/#organization", "…": "socle" },
    { "@type": "WebSite", "@id": "https://exemple.com/#website",
      "publisher": { "@id": "https://exemple.com/#organization" } },
    { "@type": "WebPage", "@id": "https://exemple.com/plombier-lyon/#webpage",
      "url": "https://exemple.com/plombier-lyon/", "name": "Plombier à Lyon",
      "isPartOf": { "@id": "https://exemple.com/#website" },
      "mainEntity": { "@id": "https://exemple.com/plombier-lyon/#service" },
      "breadcrumb": { "@id": "https://exemple.com/plombier-lyon/#breadcrumb" },
      "hasPart": { "@id": "https://exemple.com/plombier-lyon/#faq" } },
    { "@type": "Service", "@id": "https://exemple.com/plombier-lyon/#service",
      "name": "Dépannage plomberie à Lyon", "serviceType": "Dépannage plomberie",
      "category": { "@type": "Thing", "name": "Plomberie",
        "sameAs": ["https://fr.wikipedia.org/wiki/…", "https://www.wikidata.org/wiki/Q…"] },
      "provider": { "@id": "https://exemple.com/#organization" },
      "areaServed": { "@type": "City", "name": "Lyon",
        "sameAs": ["https://fr.wikipedia.org/wiki/Lyon", "https://www.wikidata.org/wiki/Q…"] } },
    { "@type": "BreadcrumbList", "@id": "https://exemple.com/plombier-lyon/#breadcrumb", "…": "…" },
    { "@type": "FAQPage", "@id": "https://exemple.com/plombier-lyon/#faq",
      "isPartOf": { "@id": "https://exemple.com/plombier-lyon/#webpage" }, "mainEntity": ["…"] }
  ]
}
```

Les `Q…` sont volontairement vides : un QID ne s'écrit jamais de mémoire.

## Les entités — relier la page à Wikidata

| Propriété | Règle | Pourquoi |
|-----------|-------|----------|
| `about` | 1 à 3 entités. Test : la page devient-elle hors sujet sans elle ? | C'est le sujet, pas le vocabulaire |
| `mentions` | 12 maximum, **visibles dans le contenu principal** (pas le menu, pas le pied de page) | Une mention invisible est une déclaration non vérifiable |
| Les deux | Une entité n'est jamais à la fois en `about` et en `mentions` | Sinon, on ne sait plus ce qui est central |

Format : `{"@type": "Thing", "name": "…", "sameAs": ["https://fr.wikipedia.org/wiki/…", "https://www.wikidata.org/wiki/Q…"]}`, en https.

**`sameAs` affirme une identité stricte.** Relier « Mercure » la planète au
QID de l'élément chimique, c'est dire aux machines une chose fausse avec
aplomb. Méfiez-vous des homonymes.

**Aucun QID de mémoire.** Chaque entité passe par le registre du projet
(`memoire/entites.csv`) : recherche Wikidata → lecture de la description →
inscription. Une entité non vérifiée part **sans `sameAs`** plutôt qu'avec
un faux. Re-vérification trimestrielle. Processus et format :
`references/entites-wikidata.md`.

**Générer et contrôler depuis le registre.** Le skill `seo-entites-triplets`
tient le registre (`memoire/entites.csv`, `memoire/triplets.csv`) et fait
dire au texte et au balisage les mêmes faits. Son script produit le
fragment `about`/`mentions` d'une page, avec les `sameAs` Wikidata, à
fusionner dans le nœud `WebPage` ; et il signale les entités nommées dans le
texte mais absentes du JSON-LD, sans `sameAs`, ou reliées à un autre QID
que celui du registre :

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/triplets.py" jsonld --about "…" --depuis page.html --url <canonical>
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/triplets.py" verifier page.html --page <slug> --strict
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/triplets.py" wikidata "<libellé>" [--site <domaine>]
```

`DefinedTerm` pour le jargon, `knowsAbout` de l'`Organization`, `provider`
du `Service`, `author` → `Person` : graphe complet dans
`seo-entites-triplets/references/jsonld-entites.md`.

## Les pièges — ceux qui coûtent une erreur en Search Console

| Piège | La règle |
|-------|----------|
| Un logiciel **cité** (outil utilisé, intégration) | `Thing` avec `sameAs`, **jamais `SoftwareApplication`** : Google appliquerait les exigences du rich result Software App (`offers`, note ou avis) → erreur critique. `SoftwareApplication` seulement si la page vend ou présente ce logiciel comme son sujet |
| Un service | `Service`, pas `Product` sans prix (erreur `offers` manquant) |
| `serviceType` | Texte libre. L'entité désambiguïsée va dans `category` |
| `areaServed` | `City` / `Country` avec `sameAs`, pas une chaîne nue |
| `SearchAction` | Supprimée : le champ de recherche sitelinks n'existe plus depuis novembre 2024 |
| `aggregateRating` sur `Organization` | Interdit : avis auto-attribués, ignorés et sanctionnables |
| `ItemList` secondaire | Reliée par `mentions`, jamais `hasPart` |
| `headline` | Égal au H1, 110 caractères maximum |
| `dateModified` | Honnête : la date de la dernière modification réelle du contenu, pas du déploiement |
| Homonymes | `disambiguatingDescription` d'une phrase sur l'`Organization` |
| Identité légale | `legalName`, `identifier` (`PropertyValue` avec le numéro d'immatriculation), `vatID` — **recopiés des mentions légales** |
| `foundingDate` | Ne pas la baliser si elle contredit ce que dit le site |
| `logo` | Version sombre (affichée sur fond blanc), URL absolue, au moins 112 × 112 px |
| `branchOf` | Remplacé : une agence pointe vers le siège par `parentOrganization` |
| Siège non ouvert au public | `Organization`, pas `LocalBusiness` ; une agence avec adresse visible = `LocalBusiness` + `parentOrganization` |
| Type local | Le sous-type précis, éventuellement plusieurs (`["GeneralContractor","HousePainter"]`), plutôt qu'une `Organization` doublée d'un `LocalBusiness` |
| Un seul `LocalBusiness`, une seule adresse | Jamais une adresse par page ville : la ville va en `Service.areaServed`, sur sa seule page, une ville par page |
| NAP | Nom, adresse, téléphone dans la même graphie que la fiche Google (« Av. » ≠ « avenue ») ; `geo` et horaires validés contre elle |
| `Service.audience` | `BusinessAudience` (le secteur, sur une page secteur) ; vocabulaire de `serviceType` identique sur tout le site |
| Catalogue de l'accueil | `hasOfferCatalog` ou `ItemList` de `Service` sans URL ; `sameAs` seulement sur la `category` — un `sameAs` sur le `Service` affirmerait qu'il **est** le concept |
| `about` / `mentions` d'un article | Sur le `BlogPosting`, pas sur la `WebPage` ; jamais aux deux endroits |
| `BreadcrumbList` | Seulement si un fil d'Ariane est visible, avec les mêmes libellés ; positions 1..n, la première = l'accueil, aucun niveau qui n'existe pas |
| FAQ multiples | Plusieurs blocs FAQ sur une page = un seul `FAQPage` ; jamais la même question sur deux pages voisines |
| `Course` | `offers` seulement si un prix est affiché (« à partir de » → `priceSpecification.minPrice`, `valueAddedTaxIncluded: false`) ; `courseMode`, `coursePrerequisites`, `teaches` seulement s'ils sont visibles |
| Santé et bien-être hors site médical | Jamais `MedicalCondition` ni `MedicalTherapy` |
| Images | L'URL d'origine en grande taille, jamais une version redimensionnée par un CDN ; pour une photo sous licence : `ImageObject` avec `creditText`, `license`, `acquireLicensePage` |
| Personnes | Pas de nœud `Person` sans profil réel ; les comptes personnels d'un fondateur vont dans le `sameAs` de la `Person`, pas de l'`Organization` ; `sameAs` sans paramètres de suivi |
| Logos clients | Non balisés sans accord écrit |
| Graphe d'une extension SEO (Yoast…) | S'aligner sur ses `@id` (Yoast : `WebPage` = l'URL sans `#webpage`, `Person` = `#/schema/person/{hash}`) plutôt que l'inverse — sinon deux nœuds page. Si sa sortie schema est coupée, vérifier qu'elle le reste après chaque mise à jour |

## L'identité de l'organisation — la réconciliation d'entité

Google et les LLM doivent comprendre que tous les noms, profils et sites
désignent **la même** organisation. C'est le socle le plus rentable, et le
plus souvent bâclé.

1. **Unifier d'abord le contenu visible** : un seul nom dans les titres,
   les mentions légales, les profils. Baliser un désordre le fige.
2. `name` = la marque ; `legalName` = la raison sociale (jamais l'inverse) ;
   `alternateName` = tous les noms en circulation (sigle, ancien nom) ; un
   nœud `Brand` si la marque diffère de la société.
3. **Groupe** : `parentOrganization` / `subOrganization`. Ne jamais
   s'attribuer la certification ou le statut partenaire d'une société sœur.
4. **Preuves** : `hasCredential` (`EducationalOccupationalCredential` avec
   `name`, `credentialCategory`, `recognizedBy`), `memberOf`, `award`,
   `founder` — seulement ce que le site montre.
5. **Identifiants** : société française → `identifier` (SIREN/SIRET) et
   `vatID` recopiés des mentions légales ; société étrangère → `taxID` avec
   l'identifiant national, jamais un SIREN inventé.
6. `foundingDate` en année seule, et seulement si elle ne contredit pas
   l'ancienneté affichée ; `numberOfEmployees` avec son périmètre (société
   ou groupe), cohérent avec le texte.
7. `WebSite` : `name` et `alternateName` (le nom de site que Google
   affiche en SERP), `inLanguage`, `publisher` → `#organization`.
8. **Personne-pivot** : si les IA reconnaissent mieux le fondateur que la
   marque (mesuré par `geo-share-of-model`), citez les deux ensemble dans
   le texte des pages clés (« Prénom Nom, fondateur de Marque »), avec
   `founder`/`worksFor` dans le graphe et le `sameAs` de la `Person`.

## Placeholders et livraison

Une donnée qu'on n'a pas (SIRET, téléphone, date) s'écrit `A_CONFIRMER`.
**Un `A_CONFIRMER`, un marqueur « à faire » ou un champ de gabarit entre
doubles accolades bloque la livraison** : le script le traite en erreur.

Format de livraison :

1. La balise propre, prête à coller, sans commentaire à l'intérieur
2. Hors de la balise :
   - **Nœuds présents** — type et `@id` de chaque nœud
   - **Données à confirmer** — ce qui manque, et qui peut le fournir
   - **Résultat du contrôle** — la sortie du script ci-dessous

## Générer

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/schema_build.py" page.json --socle socle-global.json \
  --entites memoire/entites.csv [--html] [--sortie page.jsonld]
```

Un petit fichier par page (type, URL, titre, fil d'Ariane, about, mentions,
service ou article, FAQ — format en tête du script) ; le socle vient d'un
seul fichier ; les entités se résolvent dans le registre (QID, sameAs). Le
script refuse plus de 3 about, plus de 12 mentions, une entité dans les deux,
un article sans date, auteur ou image, un fil qui ne part pas de l'accueil,
une FAQ vide ; il place about/mentions sur le `BlogPosting` pour un article,
puis valide le graphe produit (code 1 sur une erreur). On ne retouche pas le
JSON à la main : on corrige le fichier de page et on régénère.

## Valider

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/schema_validate.py" <fichier.html|fichier.jsonld|url> \
  [--socle socle-global.json] [--strict] [--json]
```

| Contrôle | Gravité |
|----------|---------|
| JSON valide | erreur — un bloc invalide est ignoré entièrement, silencieusement |
| Un seul script JSON-LD par page | attention |
| `@id` définis une seule fois, toutes les références `{"@id"}` résolues dans le graphe | erreur |
| `--socle` : nœuds du socle identiques à la référence (empreinte) | erreur |
| Propriétés requises Google par type / attendues par la méthode | erreur / attention |
| Doublons de types uniques (Organization, WebSite, Article…) | erreur |
| URL absolues, dates ISO 8601, `dateModified` ≥ `datePublished` | erreur |
| `A_CONFIRMER`, marqueur « à faire », doubles accolades de gabarit | erreur |
| `sameAs` : `https://www.wikidata.org/wiki/Q…`, Wikipédia en https | attention |
| `SoftwareApplication` hors sujet principal, `SearchAction`, note auto-attribuée, `about` > 3, `mentions` > 12, `headline` > 110 | attention |
| Plus d'un nœud page (`WebPage` ou sous-type) pour l'URL | erreur |
| `BreadcrumbList` : positions 1..n sans trou ; premier élément ≠ accueil | erreur / attention |
| `FAQPage` : question ou réponse vide ; balise HTML non acceptée dans une réponse | erreur / attention |
| `hasPart` vers un non-`CreativeWork` (liste, service, organisation, personne, lieu) ; `serviceType` non textuel | attention |
| Plusieurs villes en `addressLocality` ; `about`/`mentions` à la fois sur la page et sur l'article | attention |
| Plusieurs formes de l'hôte du site (http/https, avec ou sans www) dans les `@id` et URL | attention |

`--strict` renvoie 1 à la première erreur : c'est ce qui bloque une
livraison ou un commit. Sur une URL, le script lit le **HTML initial** —
exactement ce que voient les robots qui ne rendent pas le JavaScript.

Vérifiez toujours la **cohérence avec le contenu visible**. Un prix, une
note ou un avis balisé qui n'apparaît pas sur la page est un motif d'action
manuelle — la première cause de pénalité liée aux données structurées. Un
prix balisé égale la valeur du registre (`memoire/triplets.csv`) ;
`triplets.py coherence` trouve les pages où le texte dit autre chose.

## L'état des types en 2026

| Type | Statut | Note |
|------|--------|------|
| `Article` / `BlogPosting` / `NewsArticle` | ✅ | `author` → `Person` avec `@id` stable |
| `Organization`, `WebSite`, `WebPage` | ✅ | Le socle, sans rich result propre |
| `Service` | ✅ | Pas de rich result, mais le nœud central d'une page de service |
| `Product` + `Offer` | ✅ | Seulement pour un vrai produit avec prix affiché |
| `LocalBusiness` | ✅ | Indispensable en SEO local |
| `Person` | ✅ | Pages auteur. Fort signal E-E-A-T |
| `BreadcrumbList` | ✅ | Améliore l'affichage de l'URL |
| `Course`, `Event`, `VideoObject`, `Recipe`, `JobPosting` | ✅ | |
| `SoftwareApplication` | ⚠️ | **Seulement si le logiciel est le sujet de la page.** Cité → `Thing` |
| `Review` / `AggregateRating` | ⚠️ | Avis réels, visibles, vérifiables. Jamais sur sa propre `Organization` |
| `FAQPage` | ⚠️ | Rich result retiré de Google le 7 mai 2026 (rapport et test supprimés ensuite). Balisage valide et sans risque, mais sans bénéfice d'affichage : à garder seulement s'il reprend une FAQ réellement visible |
| `HowTo` | ⚠️ | Rich result déprécié depuis septembre 2023 |
| `SearchAction` | ❌ | Champ de recherche sitelinks retiré en novembre 2024 |
| `SpecialAnnouncement` | ❌ | Déprécié en juillet 2025 |

Annoncez ces limites. Promettre des étoiles là où Google ne les affiche plus
est la façon la plus rapide de perdre la confiance d'un client.

**Données structurées et IA** : Google n'utilise aucun schema spécial pour
ses fonctions IA, et ajouter du JSON-LD n'a pas augmenté les citations de
façon significative dans la seule étude contrôlée disponible (Ahrefs, mai
2026). ChatGPT et Perplexity lisent le JSON-LD comme du texte. Le schema
sert à la désambiguïsation et aux résultats enrichis qui restent ; **tout
fait balisé doit être visible dans la page**. Sources :
`../seo-optimisation-onpage/references/preuves-2026.md`.

## Recette et suivi

| Quand | Outil | Ce qu'on vérifie |
|-------|-------|------------------|
| Avant mise en ligne | `schema_validate.py --strict --socle` | Zéro erreur |
| Après mise en ligne | **Rich Results Test** | Ce que Google exploitera |
| | **Schema Markup Validator** | Conformité au vocabulaire, y compris sans rich result |
| | `view-source:` de la page | **Une seule** balise JSON-LD, présente dans le HTML initial |
| Mensuel | Search Console → Améliorations | Erreurs en production, sur tout le site |
| Mensuel | Crawl qui extrait le JSON-LD de chaque URL | Pages sans balisage, socle divergent |
| Trimestriel | Prompts aux IA (« Qui est [entité] ? Que fait-elle ? Où ? ») | L'entité est décrite avec les bons attributs |
| Une fois | `robots.txt` | Ouvert aux robots IA (voir `geo-llms-txt`) — sinon le balisage ne sert à personne |

Le Rich Results Test ne teste que ce que Google exploite. Un schema valide
qui n'y apparaît pas n'est pas forcément faux — il n'a simplement pas de
rich result associé.

## Livrables

- `schema/socle-source.json` → `schema/socle-global.json` — le socle, régénéré, jamais édité
- `schema/<slug>.json` — les nœuds de chaque page
- `memoire/entites.csv` — le registre des entités vérifiées (voir `seo-entites-triplets`)
- `SCHEMA-RAPPORT.md` — existant, erreurs, opportunités, résultat du contrôle
- `INSTRUCTIONS-POSE.md` — où et comment injecter selon le CMS
