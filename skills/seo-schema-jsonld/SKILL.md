---
name: seo-schema-jsonld
description: >
  Détecte, valide et génère les données structurées JSON-LD schema.org :
  Article, Product, LocalBusiness, Organization, Person, FAQPage, HowTo,
  BreadcrumbList, Event, Course, VideoObject, SoftwareApplication, Review.
  Signale les dépréciations Google. Déclencher sur "schema", "données
  structurées", "JSON-LD", "rich results", "rich snippets", "balisage",
  "schema.org", "étoiles dans Google", "extraits enrichis", "microdata".
---

# Données structurées — dire aux machines ce qu'est la page

Le schema ne fait pas ranker. Il fait **comprendre**, et il débloque des
affichages enrichis. En 2026, il a une seconde fonction, plus importante :
il aide les moteurs IA à extraire et attribuer correctement votre contenu.

## Étape 1 — Détecter l'existant

Récupérez la page et extrayez les trois formats :
JSON-LD (`<script type="application/ld+json">`), Microdata (`itemscope`),
RDFa (`vocab`, `typeof`).

**Google recommande JSON-LD.** Si vous trouvez du Microdata, proposez la
migration : c'est plus lisible, plus facile à maintenir, et ça ne dépend pas
de la structure HTML.

Cherchez aussi les **doublons** : un plugin SEO qui pose un `Article` plus un
thème qui en pose un autre créent une ambiguïté que Google résout en
ignorant les deux. C'est un cas très fréquent sur WordPress.

## Étape 2 — Valider

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/schema_validate.py" <fichier|url>
```

Trois niveaux de validation :

1. **JSON syntaxiquement valide** — une virgule en trop et tout le bloc est
   ignoré, silencieusement
2. **Conforme à schema.org** — types et propriétés existants, bonnes valeurs
3. **Conforme aux exigences Google** — les propriétés requises pour obtenir
   le rich result, qui sont plus strictes que schema.org

Vérifiez toujours la **cohérence avec le contenu visible**. Un schema qui
annonce un prix différent de celui affiché, ou une note moyenne qui ne
correspond à aucun avis visible, est un motif d'action manuelle. C'est la
première cause de pénalité liée aux données structurées.

## Étape 3 — L'état des types en 2026

| Type | Statut | Note |
|------|--------|------|
| `Article` / `NewsArticle` / `BlogPosting` | ✅ | Base de tout contenu éditorial |
| `Product` + `Offer` | ✅ | Prix, disponibilité, avis |
| `LocalBusiness` | ✅ | Indispensable en SEO local |
| `Organization` | ✅ | À poser sur la home. Socle de l'entité |
| `Person` | ✅ | Pages auteur. Fort signal E-E-A-T |
| `BreadcrumbList` | ✅ | Améliore l'affichage de l'URL |
| `VideoObject` | ✅ | Requis pour l'onglet Vidéos |
| `Event` | ✅ | |
| `Course` | ✅ | |
| `SoftwareApplication` | ✅ | |
| `Recipe` | ✅ | |
| `JobPosting` | ✅ | |
| `Review` / `AggregateRating` | ⚠️ | Uniquement sur des avis réels et vérifiables. Les faux avis balisés sont sanctionnés |
| `FAQPage` | ⚠️ | **Rich result restreint depuis août 2023** aux sites gouvernementaux et de santé. Reste utile pour les LLM |
| `HowTo` | ⚠️ | **Rich result déprécié depuis septembre 2023.** Le balisage reste valide mais n'affiche plus rien |
| `SpecialAnnouncement` | ❌ | Déprécié en juillet 2025 |

Annoncez ces limites. Promettre des étoiles là où Google ne les affiche plus
est la façon la plus rapide de perdre la confiance d'un client.

## Étape 4 — Les schemas à poser en priorité

Sur n'importe quel site, dans cet ordre :

1. **`Organization` sur la home** — avec `name`, `url`, `logo`, `sameAs`
   (tous vos profils externes), `contactPoint`. C'est le socle de votre
   entité, et c'est ce que les LLM utilisent pour savoir qui vous êtes.
2. **`BreadcrumbList` sur toutes les pages** — peu coûteux, effet immédiat
   sur l'affichage.
3. **`Article` sur le contenu éditorial** — avec un `author` de type `Person`
   lié à une vraie page auteur, `datePublished` et `dateModified`.
4. **`Person` sur les pages auteur** — avec `jobTitle`, `worksFor`,
   `sameAs`, `knowsAbout`.
5. **Le type métier** — `Product`, `LocalBusiness`, `Service` selon l'activité.

Le lien `Article.author` → `Person` → `sameAs` est ce qui construit
l'attribution. C'est ce qui manque à 90 % des sites, et c'est ce qui décide
si un LLM vous cite nommément ou non.

## Étape 5 — Générer

Templates dans `${CLAUDE_PLUGIN_ROOT}/schema/templates.json`. Règles de génération :

- Renseignez **toutes les propriétés requises**, sinon pas de rich result
- Ajoutez les recommandées quand la donnée existe vraiment
- **Jamais de valeur inventée.** Pas de note moyenne sans avis, pas de prix
  approximatif, pas de date fictive.
- Utilisez `@id` pour lier les entités entre elles plutôt que de les
  dupliquer sur chaque page
- Un seul bloc JSON-LD par page, avec un `@graph` si plusieurs entités —
  c'est plus propre et ça évite les conflits

```json
{
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "Organization", "@id": "https://exemple.com/#org", "…": "…" },
    { "@type": "WebSite", "@id": "https://exemple.com/#site",
      "publisher": { "@id": "https://exemple.com/#org" } },
    { "@type": "Article", "isPartOf": { "@id": "https://exemple.com/#site" },
      "author": { "@id": "https://exemple.com/#nathan" } }
  ]
}
```

## Étape 6 — Tester

- **Rich Results Test** de Google → ce qui sera réellement affiché
- **Schema Markup Validator** (schema.org) → la conformité au vocabulaire
- **Search Console → Améliorations** → les erreurs constatées en production,
  sur l'ensemble du site

Le Rich Results Test ne teste que ce que Google exploite. Un schema valide
qui n'y apparaît pas n'est pas forcément faux — il n'a simplement pas de
rich result associé.

## Livrables

- `SCHEMA-RAPPORT.md` — existant, erreurs, opportunités
- `schemas/` — un fichier JSON-LD par type généré
- `INSTRUCTIONS-POSE.md` — où l'insérer selon le CMS
