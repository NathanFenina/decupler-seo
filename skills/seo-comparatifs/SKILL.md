---
name: seo-comparatifs
description: >
  Produit des pages comparatives et « alternatives à X » qui captent
  l'intention commerciale : tableau de comparaison, positionnement honnête,
  schema Product, structure orientée conversion. Déclencher sur "page
  comparative", "X vs Y", "alternative à", "comparatif", "concurrent contre",
  "page versus", "meilleurs logiciels", "top 10", "page de comparaison".
---

# Pages comparatives — l'intention la plus proche de l'achat

« X vs Y » et « alternative à X » sont les requêtes les plus rentables du
SEO : celui qui les tape a un budget, un besoin identifié, et il compare
avant de signer. Le volume est faible, la conversion est élevée.

## Les trois formats

| Format | Requête visée | Quand |
|--------|---------------|-------|
| **Vous vs Concurrent** | « [vous] vs [concurrent] » | Le concurrent est connu, on vous compare déjà |
| **Alternative à Concurrent** | « alternative à [concurrent] » | Le concurrent domine le marché |
| **Comparatif de N solutions** | « meilleur [catégorie] » | Vous voulez capter en amont |

Le troisième est le plus difficile — vous êtes juge et partie — et le plus
puissant s'il est fait honnêtement.

## La règle qui décide de tout : l'honnêteté

Une page comparative malhonnête échoue sur les trois plans à la fois :

- **SEO** — le lecteur repart en trois secondes, le signal est mauvais
- **Conversion** — quelqu'un qui compare a déjà lu la page du concurrent.
  Il repère le biais immédiatement, et vous perdez sa confiance
- **GEO** — les LLM privilégient les sources qui présentent équitablement.
  Une page à charge ne sera jamais citée

Ce qu'il faut faire, et qui paraît contre-intuitif :

> **Dites dans quels cas le concurrent est le meilleur choix.**

« Si vous avez moins de 5 utilisateurs et un besoin uniquement de
facturation, [Concurrent] est plus simple et moins cher. Notre solution
devient pertinente à partir de 15 utilisateurs, quand il faut gérer les
droits par équipe. »

Cette phrase fait deux choses : elle disqualifie les prospects qui ne vous
conviennent pas (et qui auraient churné), et elle rend crédible tout le
reste de la page. C'est le paragraphe le plus rentable de la page.

## La structure

```
1. Réponse directe (40-60 mots)
   « [Vous] et [Concurrent] visent tous deux X. La différence tient à Y :
     [Vous] convient à [profil A], [Concurrent] à [profil B]. »

2. Tableau comparatif
   Les critères qui comptent pour la décision, pas 40 lignes de cases à
   cocher. 8 à 12 critères maximum.

3. Comparaison détaillée, critère par critère
   Un H2 par dimension : prix, fonctionnalités, mise en œuvre, support,
   intégrations, évolutivité. Un verdict par section.

4. « Choisissez [Concurrent] si… »
   3-4 cas concrets. Cette section rend la page crédible.

5. « Choisissez [Vous] si… »
   3-4 cas concrets, avec les preuves.

6. Ce que disent les utilisateurs
   Avis vérifiables des deux côtés, sources citées.

7. FAQ
   Les questions de migration, de coût de sortie, de compatibilité.

8. CTA
   Un essai, une démo, un devis. Un seul.
```

## Le tableau

Le point de bascule de la page. Règles :

- **Des critères de décision**, pas des fonctionnalités. « Temps de mise en
  œuvre » vaut mieux que « API REST disponible ».
- **Des valeurs factuelles**, pas des ✅/❌ arbitraires. « 149 €/mois » et
  « 2 à 3 semaines » plutôt que « Excellent » et « Limité ».
- **Une date de vérification** et un lien vers la source. Les tarifs
  changent ; un tableau non daté devient faux et vous décrédibilise.
- **Responsive** : `overflow-x: auto`, sinon le tableau casse en mobile —
  et c'est là que la moitié des gens le lisent.

## Le cadre juridique

En France, la publicité comparative est **licite** (article L.122-1 du code
de la consommation), sous conditions :

- ne pas être trompeuse
- comparer des biens ou services **répondant aux mêmes besoins**
- comparer **objectivement des caractéristiques essentielles, pertinentes,
  vérifiables et représentatives**
- ne pas dénigrer, ni tirer indûment profit de la notoriété d'une marque

En pratique : des faits sourcés et datés, pas de jugement de valeur sur
l'entreprise concurrente, pas d'utilisation de son logo de façon à créer une
confusion.

Ce cadre n'est pas une contrainte gênante : il décrit exactement la page qui
convertit le mieux.

## Le schema

`Product` ou `SoftwareApplication` pour chaque solution comparée. Le
`AggregateRating` **uniquement** s'il repose sur de vrais avis vérifiables —
une note inventée est un motif d'action manuelle.

`FAQPage` sur la section FAQ.

## Créer une série

Sur un marché à 6-8 concurrents, produisez une page par concurrent. Mais :

- **Chaque page doit être écrite spécifiquement.** Un gabarit avec le nom du
  concurrent remplacé est du contenu mince — voir les seuils de
  `/seo programmatique`.
- Reliez-les entre elles et à une page « comparatif général »
- Maintenez-les : un tableau de prix obsolète est pire que pas de page

Rythme réaliste : une page par semaine, bien faite, plutôt que huit en un
jour.

## Livrables

- `comparatif-<a>-vs-<b>.md` — le contenu
- `comparatif-<a>-vs-<b>.html` — la page prête à coller
- `tableau-comparatif.csv` — les données, à maintenir
- Le schema JSON-LD
- `SOURCES.md` — d'où vient chaque affirmation, et à quelle date
