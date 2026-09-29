# Le graphe d'entités — about, mentions, sameAs, DefinedTerm, knowsAbout

Ce fichier complète `seo-schema-jsonld` (architecture du graphe, socle,
@id, pièges) sur un point : **relier chaque entité nommée à un identifiant
stable**, et faire que le balisage dise les mêmes faits que le texte.

## Le graphe d'une page de service

Page « Bilan annuel » d'Atlas Conseil (cabinet fictif). Les `Q…` sont
volontairement vides : un QID vient du registre, jamais de la mémoire.

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://www.atlas-conseil.example/#organization",
      "name": "Atlas Conseil",
      "url": "https://www.atlas-conseil.example/",
      "logo": {
        "@type": "ImageObject",
        "@id": "https://www.atlas-conseil.example/#logo",
        "url": "https://www.atlas-conseil.example/logo-sombre.png"
      },
      "description": "Atlas Conseil est un cabinet d'expertise comptable situé à Lyon.",
      "knowsAbout": [
        {
          "@type": "Thing",
          "name": "Expertise comptable",
          "sameAs": [
            "https://www.wikidata.org/wiki/Q…",
            "https://fr.wikipedia.org/wiki/Expertise_comptable"
          ]
        },
        {
          "@type": "Thing",
          "name": "Taxe sur la valeur ajoutée",
          "sameAs": [
            "https://www.wikidata.org/wiki/Q…",
            "https://fr.wikipedia.org/wiki/Taxe_sur_la_valeur_ajout%C3%A9e"
          ]
        }
      ],
      "sameAs": [
        "https://www.linkedin.com/company/atlas-conseil-exemple"
      ]
    },
    {
      "@type": "WebSite",
      "@id": "https://www.atlas-conseil.example/#website",
      "name": "Atlas Conseil",
      "url": "https://www.atlas-conseil.example/",
      "publisher": {
        "@id": "https://www.atlas-conseil.example/#organization"
      }
    },
    {
      "@type": "WebPage",
      "@id": "https://www.atlas-conseil.example/offres/bilan-annuel/#webpage",
      "url": "https://www.atlas-conseil.example/offres/bilan-annuel/",
      "name": "Bilan annuel pour les TPE à Lyon",
      "isPartOf": {
        "@id": "https://www.atlas-conseil.example/#website"
      },
      "mainEntity": {
        "@id": "https://www.atlas-conseil.example/offres/bilan-annuel/#service"
      },
      "about": {
        "@type": "Thing",
        "name": "Bilan comptable",
        "sameAs": [
          "https://www.wikidata.org/wiki/Q…",
          "https://fr.wikipedia.org/wiki/Bilan_comptable"
        ]
      },
      "mentions": [
        {
          "@id": "https://www.atlas-conseil.example/#organization"
        },
        {
          "@type": "City",
          "name": "Lyon",
          "sameAs": [
            "https://www.wikidata.org/wiki/Q…",
            "https://fr.wikipedia.org/wiki/Lyon"
          ]
        },
        {
          "@id": "https://www.atlas-conseil.example/glossaire/#liasse-fiscale"
        }
      ]
    },
    {
      "@type": "Service",
      "@id": "https://www.atlas-conseil.example/offres/bilan-annuel/#service",
      "name": "Bilan annuel",
      "serviceType": "Établissement des comptes annuels",
      "description": "Le bilan annuel d'Atlas Conseil coûte 1 200 € HT et dure trois semaines.",
      "provider": {
        "@id": "https://www.atlas-conseil.example/#organization"
      },
      "category": {
        "@type": "Thing",
        "name": "Expertise comptable",
        "sameAs": [
          "https://www.wikidata.org/wiki/Q…"
        ]
      },
      "areaServed": {
        "@type": "City",
        "name": "Lyon",
        "sameAs": [
          "https://www.wikidata.org/wiki/Q…"
        ]
      },
      "offers": {
        "@type": "Offer",
        "price": "1200",
        "priceCurrency": "EUR",
        "availability": "https://schema.org/InStock",
        "priceSpecification": {
          "@type": "UnitPriceSpecification",
          "price": "1200",
          "priceCurrency": "EUR",
          "valueAddedTaxIncluded": false
        }
      }
    },
    {
      "@type": "DefinedTerm",
      "@id": "https://www.atlas-conseil.example/glossaire/#liasse-fiscale",
      "name": "Liasse fiscale",
      "description": "Ensemble des formulaires fiscaux joints à la déclaration de résultat.",
      "url": "https://www.atlas-conseil.example/glossaire/#liasse-fiscale",
      "inDefinedTermSet": {
        "@id": "https://www.atlas-conseil.example/glossaire/#termes"
      }
    },
    {
      "@type": "DefinedTermSet",
      "@id": "https://www.atlas-conseil.example/glossaire/#termes",
      "name": "Glossaire comptable d'Atlas Conseil",
      "url": "https://www.atlas-conseil.example/glossaire/"
    }
  ]
}
```

Ce qu'il faut y lire :

- **`about`** : un seul sujet, le bilan comptable, avec son `sameAs`.
  C'est l'entité qui doit arriver en tête de la saillance.
- **`mentions`** : trois entités, toutes visibles dans le contenu
  principal. L'organisation et le terme du glossaire sont des
  **références `@id`**, pas des copies : une seconde `Organization` recopiée
  dans `mentions` serait une entité concurrente.
- **`Service`** : `provider` → l'organisation du socle ; `category` → le
  `Thing` désambiguïsé ; `areaServed` → une `City` avec `sameAs`.
  `description` reprend **le triplet principal**, mot pour mot.
- **`Offer.price`** égale la valeur du triplet « coûte » du registre. Un
  prix balisé qui diffère du prix affiché est un motif d'action manuelle ;
  s'il n'est pas affiché, on ne le balise pas.
- **`knowsAbout`** sur l'`Organization` : les domaines d'expertise, les
  mêmes entités que les `about` et `category` des pages de service. Le socle
  étant identique sur toutes les pages, `knowsAbout` se modifie dans
  `socle-source.json`, jamais page par page. `triplets.py jsonld
  --organisation` le produit depuis le registre.

## DefinedTerm — le jargon du métier

Chaque terme que le texte définit (règle 8 de l'écriture en triplets)
devient un `DefinedTerm` :

| Propriété | Valeur |
|-----------|--------|
| `name` | Le terme, tel qu'écrit |
| `description` | **La définition du texte**, pas une autre (colonne `definition` du registre) |
| `inDefinedTermSet` | `{"@id": "…/glossaire/#termes"}` — le `DefinedTermSet` de la page glossaire |
| `@id` / `url` | L'ancre du terme sur la page glossaire, si elle existe |
| `sameAs` | Le QID, seulement si le terme a un élément Wikidata qui a exactement ce sens |

La page glossaire porte le `DefinedTermSet` (en `mainEntity` d'une
`CollectionPage` ou d'une `WebPage`) et un `DefinedTerm` par terme, avec
`@id` stable. Les autres pages les **référencent** en `mentions` par leur
`@id` — le `DefinedTerm` doit alors figurer dans leur graphe, comme dans
l'exemple ci-dessus, sinon la référence est orpheline. Sans page glossaire,
le `DefinedTerm` se pose en ligne dans `mentions`, sans `inDefinedTermSet`.

## Person — l'auteur, maillon de l'attribution

Sur chaque article : `author` → `{"@id": "https://www.atlas-conseil.example/#/schema/person/claire-martin"}`,
et ce nœud dans le graphe :

```json
{
  "@type": "Person",
  "@id": "https://www.atlas-conseil.example/#/schema/person/claire-martin",
  "name": "Claire Martin",
  "jobTitle": "Expert-comptable associée",
  "worksFor": { "@id": "https://www.atlas-conseil.example/#organization" },
  "knowsAbout": [
    { "@type": "Thing", "name": "Expertise comptable", "sameAs": ["https://www.wikidata.org/wiki/Q…"] }
  ],
  "sameAs": ["https://www.linkedin.com/in/…"]
}
```

`knowsAbout` de l'auteur ⊂ `knowsAbout` de l'organisation : un auteur qui
« sait » un domaine que le cabinet ne revendique nulle part brouille
l'entité. La chaîne article → auteur → organisation → `sameAs` est celle
qui permet à un moteur d'écrire « selon Claire Martin, expert-comptable
chez Atlas Conseil ».

## Les identifiants, par ordre de solidité

| Identifiant | Quand | Forme |
|-------------|-------|-------|
| QID Wikidata | Concept, lieu, organisation, personne publique qui a un élément | `https://www.wikidata.org/wiki/Q…` |
| Article Wikipédia | En complément du QID, dans la langue de la page | `https://fr.wikipedia.org/wiki/…` |
| Site officiel | Organisation, logiciel, texte officiel (Légifrance, BOFiP, site de l'administration) | URL https canonique |
| Profil de référence | Organisation, personne : LinkedIn, registre du commerce | URL du profil |
| `@id` interne | Toute entité décrite par le site lui-même (organisation, auteurs, termes du glossaire) | `{"@id": "…"}` |

**Identité stricte.** `sameAs` dit « c'est la même chose ». Le concept
« TVA » n'est pas le formulaire de déclaration de TVA ; la ville de Lyon
n'est pas la métropole de Lyon. En cas de doute, pas de `sameAs`.

## Contrôler

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/triplets.py" verifier page.html --page /offres/bilan-annuel/
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/schema_validate.py" page.html --socle schema/socle-global.json --strict
```

Le premier dit si les entités **du texte** sont balisées et reliées au bon
QID ; le second, si le graphe est **valide** (références résolues, pas de
doublon d'`Organization`, pas de `SoftwareApplication` pour un logiciel
cité). Il faut les deux.
