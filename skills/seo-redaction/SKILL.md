---
name: seo-redaction
description: >
  Rédige un article ou une page complète à partir d'un brief, optimisé SEO et
  GEO, dans un style humain qui ne se détecte pas comme généré. Recherche
  obligatoire avant écriture, une donnée par paragraphe, zéro chiffre inventé.
  Déclencher sur "rédige", "écris un article", "rédaction", "écris cette
  page", "produis le contenu", "article de blog", "rédige à partir du brief",
  "écris-moi un guide".
---

# Rédaction — écrire quelque chose qui mérite d'exister

La question n'est pas « comment produire 1 500 mots optimisés ». C'est
« qu'est-ce que ce texte apporte que les dix premiers résultats n'apportent
pas ». Si vous n'avez pas de réponse, ne l'écrivez pas.

## Règle zéro — chercher avant d'écrire

Interdiction d'écrire depuis les seules connaissances du modèle.

Avant la première phrase :
1. Lire le brief, ou le produire (`/seo brief`)
2. Lire réellement le top 3 (Firecrawl) — pas les résumer de mémoire
3. Vérifier chaque chiffre à sa source
4. Récupérer le vocabulaire de l'audience (Reddit, avis, forums)

**Aucun chiffre inventé. Jamais.** Un chiffre sans source ne s'écrit pas.
Si la donnée manque : soit on la trouve, soit on écrit la phrase sans elle.
« Selon une étude récente » sans référence est un aveu.

## La structure qui fonctionne

### L'ouverture — les 100 premiers mots
1. **La réponse directe**, en 40-60 mots, immédiatement. Elle sert au
   lecteur pressé, au featured snippet et aux LLM à la fois.
2. Ce que l'article couvre et pour qui.
3. Ce qui le distingue : une donnée propre, une expérience de terrain, une
   méthode.

Ce qu'il ne faut jamais écrire : « Dans un monde où le digital prend une
place croissante… ». Personne n'a jamais lu ce paragraphe. Entrez dans le
sujet à la première phrase.

### Le corps
- Un H2 = une question que le lecteur se pose vraiment
- **Un paragraphe = une idée + une preuve.** Donnée, exemple, chiffre,
  cas concret ou méthode. Un paragraphe sans preuve se supprime.
- 3-5 phrases par paragraphe. Au-delà, on ne lit plus en diagonale.
- Alternez les formats : texte, tableau, liste, encadré, exemple.
- Répondez au « comment », pas seulement au « quoi ». La profondeur
  technique est ce qui vous distingue du contenu générique.

### La conclusion
Pas de résumé. Une conclusion utile donne la prochaine action concrète et
un lien interne vers l'étape suivante.

## Le style — ne pas écrire comme une IA

Ce qui trahit un texte généré, et qu'il faut bannir :

| ❌ À proscrire | ✅ À la place |
|----------------|---------------|
| « Il est important de noter que » | Notez-le, sans l'annoncer |
| « Dans le monde d'aujourd'hui » | Entrez dans le sujet |
| « Que vous soyez X ou Y, … » | Parlez à une personne précise |
| « En conclusion, il apparaît que » | Concluez |
| « plonger », « exploiter tout le potentiel », « révolutionner » | Des verbes ordinaires |
| Toutes les phrases de même longueur | Alternez court et long |
| Trois adjectifs par nom | Un, ou aucun |
| Une liste à puces toutes les 200 mots | Des listes quand il y a une liste |
| « Il convient de souligner l'importance cruciale » | Dites la chose |

Les marqueurs d'humain, à cultiver :
- Des phrases de longueurs inégales, y compris très courtes
- Une opinion assumée, avec sa raison
- Un exemple précis, daté, chiffré, vécu
- La mention de ce qui **ne marche pas** ou de ce qu'on ne sait pas
- Un contre-argument honnête

Ce dernier point est le plus efficace : un article qui dit « cette méthode
ne convient pas si vous êtes dans ce cas » est immédiatement plus crédible
qu'un article qui vante sans réserve.

## Optimisation SEO — sobre

- Mot-clé principal : H1, dans les 100 premiers mots, un H2, la conclusion.
  **Ça suffit.** Le bourrage se voit et ne sert plus depuis longtemps.
- Variantes et synonymes naturellement répartis
- Les entités du brief mentionnées
- Hiérarchie Hn respectée, sans saut de niveau
- Ancres de liens internes descriptives
- Images avec un `alt` qui décrit vraiment l'image

## Optimisation GEO — être citable

Un LLM cite ce qu'il peut extraire proprement :

- **Réponse directe** en haut, autonome hors contexte
- **Définitions explicites** : « Le X est un Y qui permet de Z. » Une
  phrase, complète, sans référence au paragraphe précédent
- **Données chiffrées sourcées** : les LLM privilégient le vérifiable
- **Structure lisible par machine** : titres explicites, listes, tableaux
- **FAQ en fin d'article** avec des réponses de 40-60 mots
- **Cohérence de l'entité** : nommez votre marque, votre auteur, vos
  produits de la même façon partout, sur tout le site

## E-E-A-T — le prouver, pas l'affirmer

- **Expérience** : « sur les 40 audits que nous avons menés en 2025 »,
  pas « nous avons une grande expérience »
- **Expertise** : la précision du vocabulaire, les nuances, les cas limites
- **Autorité** : sources externes reconnues citées, données propres
- **Confiance** : auteur identifié avec ses credentials, date de mise à
  jour, sources vérifiables, conflits d'intérêts déclarés

## Longueur

Écrivez ce que le sujet exige. Le top 3 donne un ordre de grandeur, pas un
objectif. Un article de 900 mots qui répond complètement bat un article de
2 500 mots dont 1 600 sont du remplissage — et le remplissage se détecte
immédiatement, par les lecteurs comme par Google.

## Auto-contrôle avant remise

- [ ] Chaque chiffre a sa source
- [ ] Chaque paragraphe apporte une idée nouvelle
- [ ] La réponse directe fonctionne sortie de son contexte
- [ ] Aucune formule de la liste noire
- [ ] Un lecteur du métier apprendrait quelque chose
- [ ] Les liens internes du brief sont posés
- [ ] Rien n'est affirmé sans pouvoir être vérifié
- [ ] Vous seriez à l'aise de le signer de votre nom

## Livrables

- `article-<slug>.md` — le texte
- `article-<slug>.html` — si destiné à un CMS (`/seo page`)
- `sources.md` — chaque affirmation chiffrée et son lien
- Le schema JSON-LD correspondant (`/seo schema`)

Enchaînez : `/seo publish` pour la mise en ligne en brouillon.
