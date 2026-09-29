---
name: seo-brief
description: >
  Produit un brief rédactionnel complet à partir d'un mot-clé : intention,
  analyse SERP, plan Hn, entités à couvrir, champ sémantique, exigences
  E-E-A-T, section GEO (réponse directe, FAQ, TL;DR), maillage, schema, et
  consignes au rédacteur. Déclencher sur "brief", "brief SEO", "brief
  rédactionnel", "plan d'article", "plan Hn", "que dois-je écrire sur",
  "cahier des charges rédaction", "structure d'article", "je veux écrire sur".
---

# Brief rédactionnel — le document qui rend l'article inévitable

Un bon brief permet à quelqu'un qui ne connaît rien au SEO d'écrire un
article qui ranke. S'il faut du jugement SEO pour l'exécuter, le brief est
incomplet.

## Prérequis — collecter avant de rédiger

1. Requête cible + variantes → `/seo motscles` ou DataForSEO
2. SERP live → `/seo serp <requête>`
3. Top 3 scrapés (Firecrawl) → plans Hn, longueurs, angles
4. Questions PAA
5. Vocabulaire réel de l'audience → Reddit, forums, avis clients
6. Votre positionnement → `config` → `projet`

**Ne rédigez jamais un brief sans avoir regardé la SERP.** C'est la
différence entre un brief et une supposition.

## Structure du brief

### 1. Vue stratégique
- Requête principale, volume, difficulté, CPC
- Requêtes secondaires (5-15) avec leurs volumes
- Intention dominante, justifiée par ce que montre la SERP
- Position dans le parcours d'achat
- Objectif business de la page — trafic, lead, vente ?
- Risque zero-click IA et opportunité GEO
- **Pourquoi cette page existe** : ce qu'elle apporte que les 10 premiers
  résultats n'apportent pas. Si vous ne savez pas répondre, ne produisez
  pas la page.

### 2. Intelligence SERP
- Type de pages qui rankent
- Longueur moyenne du top 3 (une fourchette, pas un objectif de mots à
  atteindre — écrire pour remplir se voit)
- Features occupées et lesquelles viser
- Le plan Hn des 3 premiers, côte à côte
- **Les gaps** : ce qu'aucun ne traite correctement. C'est votre angle.

### 3. Architecture
- URL proposée : courte, descriptive, avec le mot-clé
- Title : 50-60 caractères, mot-clé dans les 3 premiers mots
- Meta description : 150-160 caractères, promesse + différenciation
- H1 : proche du title, pas identique
- **Plan Hn complet**, du H1 aux H3, avec pour chaque section :
  - ce qu'elle doit contenir, en une phrase
  - le nombre de mots approximatif
  - la donnée, l'exemple ou la source à y placer

### 4. Exigences de contenu
- **Entités à mentionner** : concepts, outils, normes, acteurs du domaine.
  C'est ce qui prouve la maîtrise du sujet, à Google comme aux LLM.
- **Champ sémantique** : les termes attendus. Pas pour les caser, pour
  vérifier qu'aucun sous-sujet n'est oublié.
- **Données obligatoires** : chiffres, sources, dates. Une par section.
- **Signaux E-E-A-T** : qui signe, quelle expérience de terrain à raconter,
  quelles sources externes citer.
- **Éléments visuels** : tableau, schéma, capture — à quel endroit et
  pourquoi.
- **Format spécifique** si la SERP l'impose : tableau comparatif,
  checklist, calculateur.

### 5. Section GEO — ce qui vous rend citable

C'est la partie que la plupart des briefs n'ont pas.

- **Réponse directe** : rédigez-la vous-même, 40-60 mots, à placer juste
  après le H1. Elle doit être extractible telle quelle par un LLM ou un
  featured snippet, et se suffire hors contexte.
- **TL;DR** : 3-5 puces en haut de page.
- **FAQ** : 5 questions issues des PAA, réponses de 40-60 mots dont la
  première phrase répond réellement.
- **Définitions** : les termes clés définis explicitement, en une phrase
  autonome. Les LLM extraient les définitions.
- **Statistiques citables** : au moins une donnée chiffrée sourcée, ou
  mieux, propriétaire. Une donnée originale est ce qui se fait citer.

### 6. Maillage et technique
- 3-5 liens internes sortants : page cible + ancre exacte
- Les pages qui devront lier vers cet article une fois publié
- 2-3 sources externes d'autorité à citer
- Type de schema à poser (Article, FAQPage, HowTo…)

### 7. Consignes au rédacteur
- Ton et registre (repris de `config` → `projet.ton`)
- Vouvoiement ou tutoiement
- Ce qu'il faut éviter : formules creuses, superlatifs sans preuve,
  paraphrases de l'introduction
- **Une idée neuve par paragraphe.** Un paragraphe qui n'apporte ni donnée,
  ni exemple, ni méthode ne sert à rien.
- Exemples et cas concrets attendus
- Checklist de validation avant remise

## Ce qui distingue un brief exploitable

| ❌ Brief inutile | ✅ Brief exploitable |
|------------------|---------------------|
| « Parler des avantages » | « 4 avantages, un paragraphe chacun, avec un chiffre par avantage. Les concurrents n'en citent que 2. » |
| « Article de 2 000 mots » | « Le top 3 fait 1 400-2 600 mots. Écrivez ce que le sujet exige, sans remplissage. » |
| « Optimiser pour le SEO » | « Mot-clé dans H1, premier paragraphe, un H2, et la conclusion. Pas de bourrage. » |
| « Ajouter une FAQ » | « 5 questions, les voici, réponses de 40-60 mots. » |

## Livrables

- `BRIEF-<requête>.md` — le brief complet
- `champ-semantique.csv` — les termes et entités
- La réponse directe et la FAQ **déjà rédigées** — pas à faire par le rédacteur

Enchaînez : `/seo article` pour la rédaction.
