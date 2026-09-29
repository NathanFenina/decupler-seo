---
name: seo-schema-jsonld
description: >
  Définit, génère, valide et déploie les données structurées JSON-LD
  schema.org d'un site : un seul @graph par page, socle global identique
  partout (Organization + WebSite), nœuds propres à chaque type de page
  (WebPage, Service, BlogPosting, Course, CollectionPage, FAQPage, Person),
  entités reliées à Wikidata. Signale les pièges et les dépréciations Google.
  Déclencher sur "schema", "données structurées", "JSON-LD", "rich results",
  "rich snippets", "balisage", "schema.org", "étoiles dans Google", "extraits
  enrichis", "microdata", "@graph", "Wikidata", "sameAs".
---

# Données structurées — dire aux machines ce qu'est la page

Le schema ne fait pas ranker. Il fait **comprendre**, et il débloque des
affichages enrichis. En 2026, il a une seconde fonction, plus importante :
il dit aux moteurs IA qui est l'entité, ce qu'elle fait, et de quoi parle
chaque page — sans ambiguïté possible.

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
(`memoire/entites.json`) : recherche Wikidata → lecture de la description →
inscription. Une entité non vérifiée part **sans `sameAs`** plutôt qu'avec
un faux. Re-vérification trimestrielle. Processus et format :
`references/entites-wikidata.md`.

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
| `logo` | Version sombre (affichée sur fond blanc), URL absolue |

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

`--strict` renvoie 1 à la première erreur : c'est ce qui bloque une
livraison ou un commit. Sur une URL, le script lit le **HTML initial** —
exactement ce que voient les robots qui ne rendent pas le JavaScript.

Vérifiez toujours la **cohérence avec le contenu visible**. Un prix, une
note ou un avis balisé qui n'apparaît pas sur la page est un motif d'action
manuelle — la première cause de pénalité liée aux données structurées.

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
| `FAQPage` | ⚠️ | Rich result restreint depuis août 2023 aux sites gouvernementaux et de santé. Reste utile pour les LLM |
| `HowTo` | ⚠️ | Rich result déprécié depuis septembre 2023 |
| `SearchAction` | ❌ | Champ de recherche sitelinks retiré en novembre 2024 |
| `SpecialAnnouncement` | ❌ | Déprécié en juillet 2025 |

Annoncez ces limites. Promettre des étoiles là où Google ne les affiche plus
est la façon la plus rapide de perdre la confiance d'un client.

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
- `memoire/entites.json` — le registre des entités vérifiées
- `SCHEMA-RAPPORT.md` — existant, erreurs, opportunités, résultat du contrôle
- `INSTRUCTIONS-POSE.md` — où et comment injecter selon le CMS
