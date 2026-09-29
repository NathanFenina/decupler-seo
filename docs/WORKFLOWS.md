# Les workflows

Cinq chaînes câblées bout en bout. Chacune enchaîne plusieurs outils et
plusieurs skills sans que vous ayez à orchestrer quoi que ce soit.

---

## 1 · Quick wins — ≈ 6 min

**Quand** : chaque mois. C'est le meilleur rapport effort/résultat du SEO.
**Prérequis** : Search Console. DataForSEO et Firecrawl améliorent le résultat.

```
/seo quickwins
```

**La chaîne**
1. Search Console, 90 jours → pages en position 4-20 avec des impressions
2. Tri en 4 paquets : problème de snippet · contenu insuffisant ·
   cannibalisation · presque là
3. Chiffrage du potentiel, en clics puis en euros si GA4 est branché
4. SERP live sur les requêtes retenues → top 3
5. Scrape du top 3 → plans Hn, formats, angles
6. Identification de l'écart éditorial, section par section
7. Production : nouveaux titles, metas, sections à ajouter, liens internes
8. Application si le CMS est branché
9. Enregistrement des positions de départ pour mesurer à J+21

**Ce que vous obtenez** : 10 pages maximum, chacune avec ses corrections
écrites et son gain estimé.

> Faites toujours ça **avant** d'écrire quoi que ce soit de nouveau. Une page
> en position 12 monte en trois semaines ; une page neuve prend trois mois
> pour un résultat incertain.

---

## 2 · Brief adossé à la SERP — ≈ 4 min

**Quand** : avant chaque production de contenu.

```
/seo brief "logiciel de facturation TPE"
```

**La chaîne**
1. Expansion sémantique (Ubersuggest, suggestions Google)
2. Volumes, difficulté, CPC (DataForSEO)
3. SERP live → intention réelle déduite des types de page du top 5
4. Scrape des 5 premiers → plans Hn côte à côte
5. Questions People Also Ask
6. Vocabulaire réel de l'audience (Reddit)
7. Rédaction du brief : architecture, entités, exigences E-E-A-T, maillage
8. **Réponse directe et FAQ déjà rédigées**, pas laissées au rédacteur
9. Journalisation dans Notion (base Briefs & Contenus)

---

## 3 · Article vérifié — ≈ 9 min

**Quand** : après un brief validé.

```
/seo article
```

**La chaîne**
1. Lecture du brief
2. Recherche obligatoire : lecture réelle du top 3, vérification des chiffres
3. Rédaction (agent `seo-redacteur`) — style humain, zéro chiffre inventé
4. Génération du schema JSON-LD
5. Mise en HTML si destination CMS
6. Vérification du rendu dans un navigateur réel (Chrome DevTools)
7. Publication **en brouillon** (WordPress ou Webflow)
8. Pose des liens internes entrants prévus dans le brief
9. Soumission de l'URL dans Search Console
10. Mise à jour du statut dans Notion

---

## 4 · Score de visibilité IA — ≈ 5 min

**Quand** : mensuel. C'est l'indicateur GEO de référence.

```
/seo geo https://exemple.com
/seo share-of-model
```

**La chaîne**
1. Vérification du robots.txt : les crawlers IA sont-ils autorisés ?
2. 20 questions d'acheteur posées aux moteurs (Perplexity automatisé, les
   autres à la main ou par API)
3. Relevé : qui est cité, dans quel ordre, avec quelle formulation
4. Calcul de la part de voix, pondérée par le rang
5. Comparaison aux positions Google sur les mêmes sujets
6. Benchmark des 3 concurrents
7. Diagnostic des écarts : contenu absent, non extractible, ou manque
   d'autorité
8. Quick wins 30 jours + feuille de route 90 jours

---

## 5 · Rapport mensuel — ≈ 3 min

**Quand** : le 1er de chaque mois.

```
/seo rapport
```

**La chaîne**
1. Search Console : clics, impressions, CTR, positions — M-1 **et** M-12
2. GA4 : conversions organiques, revenu, pages d'entrée
3. Positions sur les requêtes suivies
4. Couverture d'index, domaines référents, score GEO
5. Roadmap : actions réalisées, actions dont la mesure est due
6. **Croisement et explication** : pas une courbe sans sa cause
7. Section « ce qui n'a pas marché » — jamais omise
8. Les 3-5 priorités du mois suivant
9. Valeurs poussées dans Notion (base Objectifs & KPI)

Puis `/seo dashboard` pour la version visuelle partageable.

---

## Automatiser

```
/loop 30d /seo quickwins
/loop 30d /seo rapport
/loop 24h /seo veille
```

Ou via des Routines programmées. Pour la veille quotidienne, le bon
comportement est le **silence** : rien ne remonte tant qu'il n'y a rien à
signaler.

---

## Enchaîner soi-même

Les skills sont composables. Une séquence type sur un nouveau projet :

```
/seo doctor                       → brancher les outils
/seo audit https://exemple.com    → l'état des lieux
/seo fix https://exemple.com      → corriger le technique bloquant
/seo quickwins                    → les gains rapides, pour montrer un résultat
/seo maillage                     → gratuit, rapide, sous-estimé
/seo motscles                     → la stratégie de contenu
/seo cocon                        → l'architecture éditoriale
/seo brief <requête>              → puis /seo article, en boucle
/seo geo                          → la visibilité IA
/seo backlink                     → l'autorité, sur la durée
/seo rapport                      → mesurer
```

L'ordre n'est pas arbitraire : un site non crawlable annule tout le reste, et
les quick wins financent la suite en montrant un résultat en trois semaines.
