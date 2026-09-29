---
name: geo-visibilite-ia
description: >
  Audit de visibilité dans les moteurs IA (ChatGPT, Perplexity, Google AI
  Overviews, Claude, Gemini) : score GEO sur 100, analyse par moteur,
  benchmark concurrentiel, quick wins 30 jours et feuille de route 90 jours.
  Déclencher sur "GEO", "AEO", "visibilité IA", "ChatGPT ne me cite pas",
  "AI Overview", "Perplexity", "être cité par les IA", "SEO pour les LLM",
  "optimisation IA", "générative", "score GEO".
---

# Visibilité IA — être la source, pas le résultat

Une part croissante des recherches se termine dans une réponse générée, sans
clic. La question n'est plus seulement « suis-je en position 3 » mais
**« suis-je la source que le modèle cite »**.

Bonne nouvelle : ce terrain est bien moins disputé que la SERP classique, et
les leviers sont différents.

## Le score GEO sur 100

### Signaux d'autorité externe — 30 points
Ce que les modèles ont appris sur vous ailleurs que sur votre site. C'est le
bloc le plus lourd, et celui sur lequel votre site n'a aucun effet direct.

| Signal | Pts |
|--------|-----|
| Page Wikipedia ou entrée Wikidata | 8 |
| Mentions dans la presse et les médias sectoriels | 7 |
| Citations dans des études, rapports, publications | 5 |
| Interventions : podcasts, conférences, webinaires | 5 |
| Profils cohérents sur les plateformes de référence | 5 |

### Signaux communautaires — 20 points
Les LLM s'appuient massivement sur les contenus communautaires, parce qu'ils
contiennent de l'expérience réelle.

| Signal | Pts |
|--------|-----|
| Mentions sur Reddit (dans des discussions authentiques) | 8 |
| Présence sur les forums spécialisés de votre secteur | 5 |
| Avis détaillés sur les plateformes de comparaison | 4 |
| Contributions techniques (GitHub, Stack Overflow, communautés métier) | 3 |

### Signaux structurels — 25 points

| Signal | Pts |
|--------|-----|
| Schema `Organization` complet avec `sameAs` | 6 |
| Schema `Person` sur les auteurs, avec `sameAs` | 5 |
| `BreadcrumbList` et structure de site claire | 4 |
| `llms.txt` présent et à jour | 3 |
| Crawlers IA autorisés dans robots.txt | 4 |
| Cohérence de l'entité : même nom, même description partout | 3 |

### Signaux de contenu — 25 points

| Signal | Pts |
|--------|-----|
| Réponses directes de 40-60 mots en tête de page | 6 |
| Données originales, chiffrées, propriétaires | 6 |
| Définitions explicites et autonomes | 4 |
| Structure extractible : listes, tableaux, titres explicites | 4 |
| Fraîcheur et dates visibles | 3 |
| Sources externes citées et liées | 2 |

## L'analyse par moteur

Chacun a une logique différente. Un audit qui les traite en bloc ne sert à
rien.

| Moteur | Ce qui pèse | Comment y entrer |
|--------|-------------|------------------|
| **ChatGPT (recherche)** | Index de recherche + autorité perçue | Ne bloquez pas `OAI-SearchBot`. Contenu structuré, source identifiable |
| **Perplexity** | Recherche en temps réel, cite systématiquement | Le plus accessible : bonne structure + fraîcheur suffisent souvent |
| **Google AI Overviews** | Reprend largement le top 10 organique | Être dans le top 10 reste le prérequis. Puis : réponse directe extractible |
| **Claude** | Recherche web + connaissances | Sources fiables, données vérifiables, attribution claire |
| **Gemini** | Écosystème Google | Search Console, Business Profile, cohérence de l'entité Google |

Pour Google AI Overviews, le SEO classique reste le socle : sans top 10, pas
de citation. Pour Perplexity et ChatGPT, la structure et la citabilité
comptent davantage que la position.

## Mesurer réellement

Ne devinez pas. Testez.

1. Établissez **20 questions d'acheteur** — celles que quelqu'un pose avant
   d'acheter ce que vous vendez. Pas vos mots-clés : des questions.
2. Posez-les aux 5 moteurs (Perplexity via son MCP, les autres à la main ou
   via API).
3. Pour chaque réponse, relevez : les domaines cités, leur ordre, la
   formulation de la mention, et si vous y êtes.
4. Calculez votre **part de voix** : nombre de réponses où vous êtes cité,
   sur le total.

| Question | ChatGPT | Perplexity | AIO | Vous ? |
|----------|---------|------------|-----|--------|
| meilleur logiciel de facturation TPE | A, B, Wikipedia | A, C, Reddit | A, B | ❌ |
| combien coûte un ERP pour PME | B, D | B, forum | B | ✅ (3e) |

Refaites la mesure tous les mois. C'est le seul indicateur GEO qui compte.

## Le diagnostic

Pour chaque question où vous n'êtes pas cité, identifiez la cause :

1. **Vous n'avez pas de contenu sur ce sujet** → produisez-le
2. **Vous en avez, mais il n'est pas extractible** → pas de réponse directe,
   structure floue, réponse noyée au troisième écran
3. **Vous en avez, mais vous n'avez pas d'autorité** → le modèle ne vous
   connaît pas. Travail hors site nécessaire
4. **Vous bloquez les crawlers** → vérifiez robots.txt immédiatement

Le cas 4 arrive plus souvent qu'on ne croit : de nombreux sites ont bloqué
`GPTBot` en 2023 par réflexe défensif et ont oublié qu'ils bloquaient aussi
leur propre visibilité.

## Les quick wins 30 jours

1. Autoriser `OAI-SearchBot`, `PerplexityBot`, `ClaudeBot` dans robots.txt
2. Ajouter une réponse directe de 40-60 mots en tête des 10 pages
   principales
3. Poser le schema `Organization` complet, avec `sameAs` vers tous vos
   profils
4. Créer les pages auteur et leur schema `Person`
5. Publier un `llms.txt`
6. Ajouter une FAQ sur les 5 pages les plus stratégiques
7. Homogénéiser la description de l'entreprise partout : site, LinkedIn,
   annuaires, réseaux. Les modèles recoupent — les incohérences les brouillent

## La feuille de route 90 jours

**Mois 1 — Structure.** Les quick wins ci-dessus. Effet mesurable sur
Perplexity dès la 3e semaine, c'est le moteur qui réagit le plus vite.

**Mois 2 — Contenu citable.** Produire une donnée originale : une étude, un
baromètre, une enquête sur votre base clients. Une donnée qu'on ne trouve
nulle part ailleurs est ce qui se fait citer, et elle continue d'être citée
pendant des années.

**Mois 3 — Autorité externe.** Reddit et forums (voir `/seo reddit`),
relations presse sectorielles, podcasts, articles invités, entrée Wikidata.

C'est le mois 3 qui produit l'essentiel des points. C'est aussi le plus
long. Commencez-le en parallèle du mois 1.

## Livrables

- `GEO-AUDIT.md` — score détaillé, analyse par moteur, benchmark
- `mesure-citations.csv` — les 20 questions × 5 moteurs
- `PLAN-GEO-90J.md` — la feuille de route
- `llms.txt` — généré
- Les schemas d'entité
