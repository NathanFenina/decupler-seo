# Les 54 skills

Chaque skill se déclenche tout seul sur les bonnes formulations. Vous pouvez
aussi l'appeler par son nom.

---

## Diagnostic et technique

| Skill | Ce qu'il fait | Déclencheurs |
|-------|---------------|--------------|
| `seo-onboarding` | Accueille, diagnostique, configure, lance la première action | « je commence », « configure », « par où » |
| `seo-audit-360` | Audit complet, 8 agents en parallèle, score /100, plan priorisé | « audit », « analyse mon site », une URL seule |
| `seo-technique-autofix` | Détecte **et corrige** : robots, canonicals, redirections, balises | « corrige », « fix », « problèmes techniques » |
| `seo-crawl-architecture` | Crawl, arborescence, orphelines, profondeur, autorité interne | « crawl », « architecture », « pages orphelines » |
| `seo-core-web-vitals` | LCP, INP, CLS mesurés, causes, correctifs front | « CWV », « site lent », « PageSpeed » |
| `seo-indexation` | Pourquoi Google ignore vos pages, sitemaps, budget de crawl | « pas indexé », « couverture », « sitemap » |
| `seo-audit-contenu` | Un verdict et une action par page publiée : vide, morte, périmée, mince, à pousser, saine, technique — 410, 301, fusion, mise à jour ; Search Console 180 jours + carte de contenu + signaux d'obsolescence | « pages pourries », « audit de contenu », « quelles pages supprimer », « pages obsolètes » |
| `seo-migration` | Refonte sans perte : inventaire, redirections, surveillance J+90 | « migration », « refonte », « j'ai perdu du trafic après » |
| `seo-veille` | Surveillance continue, alertes diagnostiquées | « veille », « monitoring », « alerte » |

## Recherche et stratégie

| Skill | Ce qu'il fait | Déclencheurs |
|-------|---------------|--------------|
| `seo-opportunites` | Classe toutes les opportunités du client : clics gagnables × valeur du thème (lexique du métier) × facilité, et les thèmes non couverts | « opportunités », « par où commencer », « priorités » |
| `seo-cartographie` | Une ligne par page : mot-clé principal, prompt principal, et chaque mois la position sur ce mot-clé et la citation du prompt par ChatGPT, Gemini et Claude ; export Notion | « cartographie », « mot-clé principal », « prompt principal » |
| `seo-quick-wins` | Les pages en position 4-20 à rattraper, chiffrées, avec les corrections écrites | « quick wins », « gains rapides », « j'ai peu de temps » |
| `seo-keyword-research` | Volumes, intention, risque zero-click IA, arbitrage | « mots-clés », « sur quoi me positionner » |
| `seo-competitor-gap` | 4 types de gaps, benchmark GEO, plan 90 jours | « concurrents », « pourquoi ils rankent mieux » |
| `seo-cocon-semantique` | Silos, piliers, satellites, plan de maillage, calendrier | « cocon », « silo », « structurer mon contenu » |
| `seo-serp-analysis` | Intention réelle, features, format attendu, difficulté vraie | « analyse la SERP », « qui ranke sur » |
| `seo-traffic-drop` | Dater, isoler, expliquer, récupérer | « chute de trafic », « core update », « déclassé » |
| `seo-gsc-analyses` | 21 analyses Search Console prêtes à lancer : cannibalisation, CTR anormal, content decay, requêtes neuves, page à créer, Google vs LLM… | « analyse la Search Console », « cannibalisation », « CTR », « pages qui déclinent » |

## Contenu

| Skill | Ce qu'il fait | Déclencheurs |
|-------|---------------|--------------|
| `seo-brief` | Brief complet, réponse directe et FAQ déjà rédigées | « brief », « plan d'article » |
| `seo-benchmark` | Les 3 meilleures pages concurrentes lues, grille « faire mieux » : 5 axes gagnés ou la page ne sort pas | « benchmark », « faire mieux que », avant toute page neuve |
| `seo-redaction` | Rédaction SEO + GEO : anti-cannibalisation, thèse avant le plan, test anti-remplissage, sources vérifiées | « rédige », « écris un article » |
| `seo-humanisation` | Dernière passe d'écriture : retire les tics d'écriture générée en français sans toucher au fond, dans le style mesuré du client ; score /100, comparatif avant/après qui bloque tout chiffre apparu | « humanise », « ça sonne IA », « enlève les tics IA », « détecteur IA » |
| `seo-optimisation-onpage` | Note /100 par critère **puis réécrit** | « optimise cette page », « score SEO », « passe au vert » |
| `seo-meta-serp` | 3 titles, 2 metas, aperçu SERP, comptage pixel | « title », « meta description », « CTR » |
| `seo-faq-paa` | FAQ ciblant PAA, snippets et LLM, + schema | « FAQ », « People Also Ask » |
| `seo-eeat` | Score /40, verdict, correctifs localisés | « E-E-A-T », « autorité », « crédibilité » |
| `seo-comparatifs` | Pages « X vs Y » et « alternative à », cadre juridique inclus | « comparatif », « vs », « alternative à » |
| `seo-lead-magnet` | Page ressource contre email qui ranke et capture : mot-clé + prompt principal, blocs authentiques, livrable verrouillé sans cacher le contenu à Google, parcours de capture vérifiés | « lead magnet », « guide gratuit contre email », « kit à télécharger », « contenu verrouillé » |

## Structure et échelle

| Skill | Ce qu'il fait | Déclencheurs |
|-------|---------------|--------------|
| `seo-design-pages` | Design d'une page qui convertit : gabarit par type de page, placement des CTA, bannières, plan d'images (photos libres créditées `photos_libres.py`, génération), tokens, signatures d'interface générée, rendu mesuré (`rendu.py`), checklist avant publication | « design de la page », « où mettre les CTA », « bannière », « plan d'images » |
| `seo-page-builder-html` | Pages HTML autonomes, prêtes à coller, avec 15 composants (hero, sommaire, chiffres clés, tableau, témoignages, lead magnet, auteur…) | « page HTML », « Elementor », « landing page » |
| `seo-programmatique` | Pages à l'échelle, garde-fous anti-contenu mince, part de contenu unique mesurée sur le lot (`similarite_lot.py`) ; pages ville d'un prestataire sans local (`areaServed`, preuve chiffrée, comparatif) | « pages à l'échelle », « pages ville », « pSEO » |
| `seo-maillage-interne` | Orphelines, flux d'autorité, règles de pose des ancres (contexte négatif, lot programmé), plan de liens exécutable | « maillage », « liens internes » |
| `seo-schema-jsonld` | Détection, validation, génération, dépréciations | « schema », « JSON-LD », « rich results » |
| `seo-entites-triplets` | Faits en triplets sujet — prédicat — objet, entités reliées à Wikidata, JSON-LD `about`/`mentions`, cohérence des valeurs sur tout le site ; trio sémantique de l'organisation et de ses auteurs (fiche d'identité vérifiée au registre, un `@id` par entité, page d'entité) | « triplets », « entités », « knowledge graph », « cohérence des faits », « trio sémantique » |
| `seo-hreflang-i18n` | Validation et génération hreflang, architecture i18n | « hreflang », « multilingue », « international » |
| `seo-images` | Poids, formats, alt, lazy loading, impact LCP et CLS | « images », « WebP », « alt » |

## GEO — moteurs IA

| Skill | Ce qu'il fait | Déclencheurs |
|-------|---------------|--------------|
| `geo-visibilite-ia` | Score GEO /100, analyse par moteur, roadmap 90 jours | « GEO », « ChatGPT ne me cite pas », « AI Overview » |
| `geo-citation-tracker` | Pourquoi **cette page** n'est pas citée, réponse directe réécrite | « rendre citable », « extractibilité » |
| `geo-llms-txt` | llms.txt, crawlers IA, entité, Wikidata, cohérence de marque | « llms.txt », « GPTBot », « entité » |
| `geo-share-of-model` | Part de voix mesurée, suivi mensuel, benchmark | « share of model », « suivi des citations » |
| `geo-linkedin` | Articles LinkedIn (page entreprise ou profil) qui servent la citation par les IA et l'entité sans dupliquer le site : format, angle, faits, anti-duplication, fiche de publication manuelle, mesure à J+30 | « article LinkedIn », « page entreprise », « newsletter LinkedIn » |

## Autorité et acquisition

| Skill | Ce qu'il fait | Déclencheurs |
|-------|---------------|--------------|
| `seo-netlinking` | Profil, prospection (dont ceux qui rankent déjà sur vos requêtes), qualification /20, classement des cibles /100 (`netlinking_score.py`), emails rédigés, séquence et suivi | « backlinks », « netlinking », « link building » |
| `seo-reddit-communautes` | Threads à valeur LLM, réponses rédigées, vocabulaire audience | « Reddit », « forums », « communautés » |
| `seo-local` | Google Business Profile, NAP, avis, pages zones sans doorway | « SEO local », « fiche Google », « pages ville » |
| `seo-digital-pr` | Études, baromètres, outils : ce qui se cite tout seul | « étude », « linkbait », « données originales » |

## Pilotage autonome

| Skill | Ce qu'il fait | Déclencheurs |
|---|---|---|
| `seo-nouveau-projet` | Crée le dépôt privé d'un site : mémoire, config, méthode embarquée, routines | « nouveau projet », « nouveau client » |
| `seo-cycle` | Le cycle des routines : veille, optimisation, contenu, rapport | « lance le cycle », « mode optimisation » |
| `seo-pilotage` | Tableau de bord partagé et roadmap : propositions du mois, validation par le client, exécution par les routines, suivi jusqu'au résultat | « roadmap », « tableau de bord », « actions à valider », « lance les tâches validées » |
| `seo-journal-mesure` | Journalise chaque modification, la mesure à J+28 contre un témoin, propose les retours arrière | « est-ce que ça a marché », « bilan » |

## Production et pilotage

| Skill | Ce qu'il fait | Déclencheurs |
|-------|---------------|--------------|
| `seo-publication-cms` | WordPress, Webflow, générique. Sauvegarde et vérification. Extensions WordPress prêtes : `templates/wordpress/` (seo-meta-rest, seo-crawl-fix, seo-entite) | « publie », « mets en ligne » |
| `seo-pilotage-notion` | 5 bases : leads, objectifs, roadmap, contenus, backlinks | « Notion », « pilotage », « roadmap » |
| `seo-reporting` | Rapport avec les **causes**, pas seulement les courbes | « rapport », « bilan mensuel » |
| `seo-dashboard` | Tableau de bord HTML autonome, partageable | « dashboard », « rapport visuel » |
| `seo-ecommerce` | Facettes, catégories, fiches, produits morts, pagination | « e-commerce », « fiches produit », « facettes » |

---

## Les règles communes

Tous les skills appliquent les mêmes principes :

1. **Jamais de chiffre inventé.** Donnée absente = « nécessite tel outil ».
2. **Toujours quantifier.** Un nombre de pages, un volume d'impressions.
3. **Chaque constat a son correctif exact**, écrit, prêt à appliquer.
4. **Maximum 5 items critiques.** Une liste de 40 problèmes n'est jamais traitée.
5. **Ne jamais bloquer sur un outil manquant.** Dire ce qui n'est pas couvert
   et continuer avec ce qu'on a.
