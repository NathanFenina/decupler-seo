---
name: seo-ecommerce
description: >
  SEO e-commerce : architecture catégories/produits, gestion des facettes et
  du gonflement d'index, fiches produit, produits en rupture ou supprimés,
  pagination, schema Product, cannibalisation catégorie/produit. Déclencher
  sur "e-commerce", "boutique en ligne", "fiches produit", "pages catégorie",
  "facettes", "filtres", "Shopify", "PrestaShop", "WooCommerce", "produit
  épuisé", "SEO boutique".
---

# SEO e-commerce — les problèmes qui n'existent que là

Un e-commerce cumule des difficultés propres : des milliers d'URL générées
automatiquement, des contenus dupliqués par construction, un catalogue qui
change tous les jours. Les recettes du SEO éditorial ne s'y appliquent pas.

## 1. L'architecture

```
Accueil
└── Catégorie                    ← la page qui ranke sur les requêtes génériques
    └── Sous-catégorie           ← les requêtes plus précises
        └── Produit              ← les requêtes de marque et de référence
```

Règle : **la page catégorie vise le terme générique**, la fiche produit vise
la référence précise. Optimiser une fiche produit sur « chaussures de
running » est une erreur : c'est le rôle de la catégorie.

Profondeur : trois clics maximum de la home au produit. Au-delà, les
produits ne sont plus crawlés régulièrement.

## 2. Les facettes — le sujet numéro un

Un filtre par couleur, taille, prix et marque génère des milliers d'URL
combinatoires. Non maîtrisé, cela sature le budget de crawl et gonfle
l'index de pages quasi identiques.

La règle de décision :

| Type de facette | Traitement |
|-----------------|------------|
| **Demande de recherche réelle** (« robe rouge », « iPhone 128 Go ») | Page **indexable**, avec un titre, une meta et un texte propres |
| **Filtre utile mais sans demande** (tri par prix, affichage par 48) | `noindex, follow` ou canonical vers la catégorie |
| **Combinaison de 3+ facettes** | `Disallow` dans robots.txt |
| **Paramètres techniques** (session, tracking) | `Disallow` + canonical |

Le travail consiste à **identifier les 20-50 facettes qui ont un volume de
recherche** et à ne rendre indexables que celles-là. Toutes les autres sont
du bruit.

Test : si personne ne cherche « chaussures bleues taille 42 en promotion »,
cette page n'a aucune raison d'exister pour Google.

## 3. Les pages catégorie

C'est là que se gagne l'essentiel du trafic e-commerce, et c'est le plus
souvent négligé.

- Un texte d'introduction **utile** (100-200 mots), pas un bloc de
  mots-clés relégué sous les produits
- Un guide d'achat, ou un lien vers celui-ci
- Un maillage vers les sous-catégories et les catégories proches
- Une FAQ sur les questions d'achat de la catégorie
- Le schema `CollectionPage` + `BreadcrumbList`

Ne mettez pas 800 mots sous la grille de produits. Personne ne les lit, et
Google le sait. 150 mots pertinents en haut valent mieux.

## 4. Les fiches produit

**Le problème structurel** : la description du fabricant est identique chez
tous les revendeurs. Vous êtes en duplication avec cent concurrents.

Ce qui différencie :
- Une description propre, écrite par vous
- Vos photos, pas celles du catalogue fournisseur
- Les avis clients (contenu unique, renouvelé, et signal de confiance)
- Les questions/réponses
- Les informations concrètes : délai réel, compatibilités, cas d'usage
- Une vidéo ou un test

Sur un catalogue de 5 000 références, vous ne pouvez pas tout réécrire.
**Concentrez l'effort sur les 200 produits qui font 80 % du chiffre.** Le
reste peut vivre avec la description fournisseur.

Schema `Product` avec `Offer` (prix, disponibilité, devise), `AggregateRating`
uniquement s'il repose sur de vrais avis, et `sku`/`gtin`.

## 5. Les produits en rupture ou supprimés

Le cas le plus mal traité de l'e-commerce, et il coûte cher.

| Situation | Ce qu'il faut faire | Ce qu'il ne faut pas faire |
|-----------|--------------------|-----------------------------|
| Rupture temporaire | Garder la page en 200, `availability: OutOfStock`, proposer une alerte de réapprovisionnement et des alternatives | Retirer la page |
| Fin définitive, remplaçant existe | 301 vers le remplaçant | 301 vers la catégorie ou la home |
| Fin définitive, pas de remplaçant | Garder la page avec des alternatives, ou 301 vers la catégorie | 404 sans alternative |
| Produit saisonnier | Garder toute l'année | Supprimer chaque saison |

Une page produit qui a accumulé de l'autorité et des avis pendant deux ans
ne doit pas être supprimée parce que le produit ne se vend plus. Vous
perdriez le trafic, les liens et les avis.

## 6. La pagination

- URL propres et crawlables : `/categorie/?page=2`
- Chaque page paginée : canonical **auto-référente**, pas vers la page 1
- `rel="next"`/`rel="prev"` ne sont plus utilisés par Google — inutile de
  les ajouter
- Une page « tout afficher » si elle reste raisonnable en poids
- Ne bloquez pas la pagination : c'est par elle que Google découvre les
  produits profonds

Erreur fréquente : canonical de toutes les pages paginées vers la page 1.
Résultat : les produits des pages 2 et suivantes ne sont plus découverts.

## 7. La cannibalisation catégorie / produit

Quand une fiche produit et sa catégorie visent la même requête, elles se
concurrencent. Symptôme : les deux oscillent en position 8-15 sans jamais
percer.

Diagnostic dans GSC : deux URL sur la même requête, avec des positions
proches. Correctif : différencier les cibles, et renforcer le maillage vers
celle qui doit gagner (en général la catégorie).

## 8. Le suivi qui compte

Segmentez tout par type de page. Une moyenne sur l'ensemble d'un e-commerce
ne veut rien dire.

| Segment | À surveiller |
|---------|--------------|
| Catégories | Positions sur les termes génériques, trafic |
| Produits | Taux d'indexation, trafic de marque |
| Facettes indexables | Est-ce qu'elles rankent, ou juste qu'elles existent ? |
| Éditorial (guides) | Trafic amont, et surtout : mène-t-il aux catégories ? |

Créez des sitemaps séparés par segment : le rapport de couverture GSC
devient enfin exploitable.

## Livrables

- `ECOMMERCE-AUDIT.md` — par segment
- `facettes.csv` — décision par facette : indexable, noindex, disallow
- `produits-morts.csv` — les ruptures et suppressions, avec la décision
- `PLAN-CATEGORIES.md` — le contenu à ajouter, catégorie par catégorie
- `product.jsonld` — le gabarit de schema
