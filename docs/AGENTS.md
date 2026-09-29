# Les 15 agents

Les agents sont des spécialistes que les skills invoquent. Sur un audit
complet, huit tournent **en parallèle** : c'est ce qui fait passer un audit
de quarante minutes à six.

| Agent | Spécialité |
|-------|-----------|
| `seo-technique` | Crawlabilité, indexabilité, robots, canonicals, redirections, sécurité, rendu JS |
| `seo-performance` | Core Web Vitals mesurés, décomposition du LCP, tâches longues, CLS |
| `seo-contenu` | Qualité, profondeur, contenu mince, duplication, cannibalisation, lisibilité |
| `seo-redacteur` | Rédaction SEO + GEO, style humain, recherche obligatoire, sources vérifiées |
| `seo-data` | Search Console, GA4, DataForSEO. La source de vérité chiffrée |
| `seo-serp` | Lecture de SERP, intention réelle, features, difficulté véritable |
| `seo-schema` | JSON-LD, validation, dépréciations, chaîne d'entité |
| `seo-geo` | Citabilité par les moteurs IA, extractibilité, réponse directe |
| `seo-netlinking` | Profil de liens, prospection, qualification, outreach |
| `seo-frontend` | Design des pages (gabarit, CTA, bannières, images), HTML autonome, CSS scopé, accessibilité, correctifs de performance |
| `seo-crawler` | Crawl, architecture, orphelines, profondeur, PageRank interne |
| `seo-strategiste` | Priorisation, séquencement, arbitrages, roadmap |
| `seo-publisher` | Publication CMS, sauvegarde, vérification post-mise en ligne |
| `seo-analyste-concurrence` | Gaps, benchmark, profils de liens, visibilité IA comparée |
| `seo-manager` | Pilote un projet : lit la mémoire, décide sur les données, délègue, journalise. Utilisé par les routines |

## Les invoquer directement

```
Utilise l'agent seo-technique sur https://exemple.com
Lance seo-serp et seo-analyste-concurrence en parallèle sur "logiciel de facturation"
```

## Ce qu'ils ont en commun

Tous appliquent les mêmes règles :

- **Jamais de chiffre inventé.** Donnée absente = « nécessite tel outil ».
- **Toujours quantifier.** « 23 pages concernées, 3 400 impressions en jeu »,
  jamais « plusieurs pages sont affectées ».
- **Chaque constat s'accompagne du correctif exact**, pas d'un conseil vague.
- **Maximum 5 items critiques.** Au-delà, ils ne le sont pas tous.
