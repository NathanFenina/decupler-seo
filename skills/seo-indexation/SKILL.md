---
name: seo-indexation
description: >
  Diagnostique et corrige les problèmes d'indexation : pages découvertes non
  indexées, explorées non indexées, sitemaps, robots.txt, canonicals,
  duplication, budget de crawl. Déclencher sur "indexation", "pas indexé",
  "mes pages n'apparaissent pas", "découverte actuellement non indexée",
  "explorée actuellement non indexée", "couverture", "sitemap", "Google ne
  voit pas mes pages", "désindexation", "j'ai disparu de Google".
---

# Indexation — pourquoi Google ignore vos pages

Une page non indexée ne rapporte rien, quelle que soit sa qualité. Avant
d'optimiser quoi que ce soit, assurez-vous que Google la voit.

## Diagnostic en 4 questions, dans cet ordre

**1. La page est-elle accessible ?** → code 200, pas de blocage robots.txt,
pas de mur d'authentification, pas de blocage géographique.

**2. Est-elle autorisée à l'index ?** → pas de `noindex` (meta, header
`X-Robots-Tag`, ou plugin SEO), canonical auto-référente ou pointant vers
une page indexable.

**3. Google la connaît-elle ?** → présente dans le sitemap, liée depuis au
moins une page interne indexée.

**4. Google la juge-t-elle digne de l'index ?** → c'est là que se joue
l'essentiel des cas difficiles.

## Décoder les statuts Search Console

| Statut GSC | Ce que ça signifie vraiment | Correctif |
|------------|------------------------------|-----------|
| **Découverte, actuellement non indexée** | Google connaît l'URL mais n'a pas jugé utile de la crawler. Signal de **qualité perçue faible** ou de budget de crawl saturé. | Renforcer le maillage interne vers la page, améliorer le contenu, réduire le bruit d'URL du site |
| **Explorée, actuellement non indexée** | Google a lu la page et a décidé de ne pas la garder. **C'est un jugement de valeur.** | Le contenu n'apporte rien d'unique. Enrichir substantiellement ou fusionner avec une autre page |
| **Page en double sans URL canonique** | Google a choisi une autre page comme canonique | Différencier les contenus, ou assumer la canonical |
| **Autre page avec balise canonique** | Vous pointez ailleurs | Vérifier que c'est voulu |
| **Exclue par la balise noindex** | Volontaire ou accidentel | Vérifier les 3 emplacements possibles |
| **Soft 404** | Page vide, ou redirection massive vers la home | Contenu réel, ou vrai 404/410 |
| **Anomalie lors de l'exploration** | 5xx, timeout, blocage pare-feu | Vérifier les logs serveur et le WAF |

Le piège classique : un WAF ou un anti-bot qui bloque Googlebot. Testez avec
l'outil d'inspection d'URL de Search Console — pas avec votre navigateur.

## « Explorée, actuellement non indexée » : le vrai sujet

C'est le statut le plus fréquent et le plus mal compris. Google ne dit pas
« il y a une erreur technique ». Il dit **« cette page n'apporte rien que je
n'aie déjà »**.

Causes réelles, par fréquence :
1. Contenu quasi identique à d'autres pages du site (pages ville, pages
   produit générées, variantes de catégorie)
2. Contenu mince — moins de 300 mots utiles
3. Page générée automatiquement sans valeur propre
4. Aucun signal de qualité : zéro lien interne, zéro lien externe
5. Site entier jugé de faible qualité — dans ce cas la page individuelle
   n'est pas le problème

Correctif : **enrichir ou fusionner**. Forcer l'indexation d'une page vide
via l'API ne fonctionne pas durablement — Google la ressortira.

## Sitemaps

Règles :
- Une URL par sitemap, uniquement des URL **indexables et canoniques**
- 50 000 URL et 50 Mo max par fichier, sinon découper via un index
- `<lastmod>` sincère. Un lastmod à la date du jour sur tout le site est
  ignoré, voire pénalisant en crédibilité
- Pas de `<priority>` ni `<changefreq>` : Google ne les utilise plus
- Déclaré dans robots.txt **et** soumis dans Search Console
- Sitemaps séparés par type (pages, articles, produits, images) : le rapport
  de couverture devient lisible par segment

Erreur fréquente : laisser dans le sitemap des URL en 301 ou en noindex.
Ça gaspille le budget de crawl et brouille le signal.

## Budget de crawl (au-delà de ~10 000 URL)

Sous 10 000 pages, le budget de crawl n'est presque jamais le problème.
Au-delà, cherchez :

- Facettes et filtres combinables → explosion combinatoire d'URL
- Paramètres de tri, de pagination, de session
- Résultats de recherche interne indexables
- Versions imprimables, AMP orphelines
- Redirections en chaîne, qui consomment un crawl par saut

Correctifs : `Disallow` sur les motifs d'URL inutiles, canonical vers la
version propre, `noindex, follow` sur les pages nécessaires à la navigation
mais sans intérêt en recherche, aplatir les chaînes de redirection.

## Accélérer l'indexation d'une page neuve

1. La lier depuis une page déjà bien crawlée (la home ou un hub, pas une
   archive de blog)
2. La mettre dans le sitemap avec un `lastmod` juste
3. Inspection d'URL dans Search Console → « Demander l'indexation »
4. La citer depuis une source externe déjà crawlée souvent

Ce qui ne marche pas : les services d'indexation payants, le spam de
demandes d'indexation, l'API Indexing en dehors de son périmètre officiel
(offres d'emploi et vidéos en direct uniquement).

## Livrables

- `INDEXATION-RAPPORT.md` — état par segment, causes, correctifs
- `non-indexees.csv` — URL, statut GSC, cause diagnostiquée, action
- `sitemap-corrige.xml` — si régénération nécessaire
