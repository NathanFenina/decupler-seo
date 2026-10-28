# Ce qui est prouvé en SEO on-page et GEO — relevé du 28/10/2026

Chaque règle de la méthode s'appuie sur une source. Niveaux de preuve :
**PROUVÉ** (documentation officielle ou expérience contrôlée) · **ÉTUDE**
(corrélation à grande échelle) · **LABO** (expérience académique, portée
limitée) · **AVIS** (Googler ou expert reconnu) · **SPÉC.** (brevet, fuite,
interprétation). À relire chaque trimestre : ce domaine bouge vite.

## Le cadre

- **Pour Google, le GEO, c'est du SEO.** Les fonctions IA reposent sur les
  systèmes de classement habituels, la génération augmentée par la recherche
  et le *query fan-out*. Inutiles selon Google : découper le texte en petits
  morceaux, llms.txt, balisage ou schema « pour l'IA », réécriture « pour
  l'IA ». Interdit : une page par variante de requête (abus de contenu à
  grande échelle). « There's no ideal page length. » — *Optimizing your
  website for generative AI features*, Google, mai 2026, MAJ 10/07/2026,
  developers.google.com/search/docs/fundamentals/ai-optimization-guide.
  **PROUVÉ** (ne vaut que pour Google).
- **Les preuves académiques GEO sont solides seulement une fois le document
  récupéré** ; les effets sur la découvrabilité restent faibles ou
  observationnels (revue arXiv 2607.14035, 07/2026 ; C-SEO Bench, NeurIPS
  2025 : 3 combinaisons positives sur 54). **LABO.**
- **Le classement reste le prérequis** : 37,9 % des URL citées par les AI
  Overviews sont dans le top 10, 31,2 % en positions 11-100 (Ahrefs,
  03/2026) ; les citations de ChatGPT viennent surtout de son canal de
  recherche, proche du top Bing (Seer, 2024). **ÉTUDE.**

## Mot-clé et entités

| Règle | Source | Niveau |
|---|---|---|
| Aucun quota de densité ni d'occurrences ; la répétition, même en variantes, enfreint les règles anti-spam | SEO Starter Guide, Google, MAJ 12/2025 | PROUVÉ |
| Densité moyenne 0,04 % dans le top 10, aucune corrélation avec la position | Rankability, 09/2026, 1 536 résultats | ÉTUDE |
| Le bourrage fait baisser la visibilité dans les réponses génératives (−8,3 %) | Aggarwal et al., GEO, KDD 2024 | LABO |
| Couvrir l'entité, ses attributs et synonymes plutôt que chaque variante | Guide IA Google 2026 | PROUVÉ |
| Title proche de la requête en langage naturel : similarité prompt ↔ title 0,60 pour les pages citées contre 0,48 | Ahrefs, 04/2026, 1,4 M de prompts | ÉTUDE |
| Titles sur-optimisés en correspondance exacte : moins cités (2,8 contre 5,9) | SE Ranking, 11/2025 | ÉTUDE |
| Title, H1 et meta alignés, sujet principal sans ambiguïté | Bing, 10/2025 | PROUVÉ (Bing) |
| Slug lisible de 4 à 7 mots : cité un peu plus souvent ; effet presque nul sur le classement Google | Ahrefs 04/2026 ; Starter Guide | ÉTUDE / PROUVÉ |

## Passages citables et fan-out

| Règle | Source | Niveau |
|---|---|---|
| AI Overviews et AI Mode lancent plusieurs recherches sur les sous-thèmes | Doc AI features, Google, MAJ 12/2025 | PROUVÉ |
| Documents découpés en passages sous intertitres, résumés et regroupés en thèmes devenus sous-requêtes | Brevet US12158907B1 (2024) | SPÉC. |
| Couvrir 8 à 15 sous-questions dans la même page, une section par sous-question | iPullRank, 11/2025 | AVIS |
| Sections de 120 à 180 mots : 4,6 citations contre 2,7 sous 50 mots | SE Ranking, 11/2025 | ÉTUDE |
| Ne pas micro-découper le contenu pour l'IA | Danny Sullivan, 01/2026 | AVIS (Google) |
| Ouvrir une section par 1 à 2 phrases compréhensibles hors contexte | Bing, 10/2025 | PROUVÉ (Bing) |
| 92 % des citations AI Mode / Gemini sont des phrases complètes de 6 à 20 mots | Bright Data, 03/2026 | ÉTUDE |
| 44 % des citations ChatGPT viennent du premier tiers du texte ; 75 % (AI Mode, Gemini) de la première moitié | K. Indig 02/2026 ; Bright Data 03/2026 | ÉTUDE |
| Intertitres précis, jamais « En savoir plus » ; questions seulement pour de vraies questions (résultats contradictoires) | Bing 10/2025 ; SE Ranking ; Semrush | PROUVÉ / ÉTUDE |
| Contenu clé en HTML visible : pas dans un onglet, un PDF ou une image | Bing, 10/2025 | PROUVÉ (Bing) |

## Preuves et apport d'information

| Règle | Source | Niveau |
|---|---|---|
| Citations d'experts +41 %, statistiques +31 %, sources citées +28 %, fluidité +28 % ; gain maximal pour les pages classées 5e | Aggarwal et al., GEO, KDD 2024 | LABO |
| 19 données chiffrées et plus : 5,4 citations contre 2,8 ; citations d'experts : 4,1 contre 2,4 | SE Ranking, 11/2025 | ÉTUDE |
| Contenu original, non interchangeable, que l'IA ne produirait pas seule | Helpful content (MAJ 10/2026) ; guide IA 2026 ; Mueller 05/2025 | PROUVÉ |
| Test pratique : au moins 3 éléments absents du top 10 et de la réponse d'un LLM (donnée propre, test, cas chiffré, expert interne, photo originale, grille de décision) | Méthode dérivée du guide IA 2026 | AVIS |
| Mots rares ≠ information nouvelle (+6 %, 0 % sur Perplexity) | Aggarwal et al. | LABO |
| Jamais de chiffre inventé : une statistique fabriquée peut être reprise et dégrader la qualité | Revue arXiv 2607.14035 | LABO |

## Fraîcheur, auteur, données structurées

| Règle | Source | Niveau |
|---|---|---|
| Les assistants citent des pages 25,7 % plus récentes que la SERP | Ahrefs, 07/2025, 17 M de citations | ÉTUDE |
| Ne jamais changer la date sans changement substantiel du contenu | Helpful content, Google, MAJ 10/2026 | PROUVÉ |
| Date « Publié / Mis à jour » visible, identique à `datePublished` / `dateModified` ISO 8601 avec fuseau | Doc dates de signature, Google | PROUVÉ |
| `author` = `Person` avec `url` vers une page auteur unique ou `sameAs` | Doc Article, Google, MAJ 09/2026 | PROUVÉ |
| E-E-A-T n'est pas un facteur en soi ; travailler qui, comment, pourquoi (signature, parcours, méthode, mention de l'IA) | Starter Guide ; Helpful content | PROUVÉ |
| Aucun schema spécial pour l'IA | Doc AI features ; guide IA 2026 | PROUVÉ |
| Rich results FAQ retirés de Google le 07/05/2026 ; HowTo depuis 09/2023 ; balisage toujours valide | SEJ, 05/2026 | PROUVÉ |
| Ajouter du JSON-LD n'augmente pas les citations IA de façon significative | Ahrefs, 05/2026, 1 885 pages contre 4 000 témoins | ÉTUDE |
| Tout fait balisé doit être visible en HTML | Google, 05/2025 | PROUVÉ |

## Maillage, title, crawlers, mesure

| Règle | Source | Niveau |
|---|---|---|
| Liens `<a href>` crawlables ; pas de nombre idéal ; ancres descriptives, sans mots-clés forcés | Doc liens, Google, MAJ 12/2025 | PROUVÉ |
| Variété d'ancres corrélée au trafic ; au moins une ancre exacte aide | Zyppy, 23 M de liens internes | ÉTUDE |
| 76 % des titles réécrits par Google (T1 2025) ; 51-60 caractères les moins réécrits | SEL 05/2025 ; Zyppy | ÉTUDE |
| OAI-SearchBot, Claude-SearchBot, PerplexityBot à autoriser pour exister dans ChatGPT, Claude, Perplexity ; GPTBot, ClaudeBot, Google-Extended = choix sur l'entraînement | Docs OpenAI, Anthropic, Perplexity, Google (10/2026) | PROUVÉ |
| Les robots IA (hors Gemini) ne rendent pas le JavaScript : contenu principal dans le HTML initial | Vercel / MERJ, 12/2024 | ÉTUDE |
| llms.txt ignoré par Google ; 97 % des fichiers jamais demandés | Guide IA 2026 ; Ahrefs 06/2026, 137 210 domaines | PROUVÉ / ÉTUDE |
| Search Console : rapport « Generative AI performance » (impressions, sans clics), ouvert à tous depuis le 31/08/2026 ; Bing : rapport « AI Performance » (préversion) | Google Search Central, 06/2026 | PROUVÉ |
| Les réponses varient : plusieurs exécutions par prompt pour un suivi fiable | Revue arXiv 2607.14035 | LABO |

## Non vérifié — ne pas présenter comme établi

« 85 % des citations AI Overviews de moins de 2 ans » (Seer), « 17 % du
top 10 » (BrightEdge), signaux « ABC » du procès antitrust, schema qui
« aide Copilot » (propos de conférence), interrupteur Search Console de
refus des fonctions IA.
