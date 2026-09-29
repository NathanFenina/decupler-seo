---
name: seo-migration
description: >
  Pilote une refonte ou migration de site sans perdre de trafic : inventaire,
  plan de redirections 301, mapping ancien/nouveau, checklist pré et post
  mise en ligne, surveillance J+1 à J+90. Déclencher sur "migration",
  "refonte", "changement de domaine", "je change de CMS", "nouveau site",
  "redirections", "plan de redirection", "passage en HTTPS", "j'ai refait mon
  site et j'ai perdu du trafic".
---

# Migration — l'opération où l'on perd le plus vite

Une refonte ratée coûte 40 à 70 % du trafic organique, et la récupération
prend 6 à 12 mois. Presque toujours pour la même raison : **le plan de
redirections a été fait après la mise en ligne, pas avant.**

Ce skill sert autant à préparer une migration qu'à réparer celle qui vient
de mal se passer.

## Phase 1 — Inventaire de l'existant (avant tout)

À faire **pendant que l'ancien site est encore en ligne**. Une fois éteint,
la donnée est perdue.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/crawl_site.py" <ancien-site> --max 5000 --exporter inventaire.csv
```

Croisez trois sources :
1. **Crawl** — toutes les URL accessibles
2. **Search Console** — 16 mois de pages qui reçoivent des impressions
3. **Backlinks** (Ahrefs) — les URL qui reçoivent des liens externes

Cette troisième source est celle qu'on oublie. Une page sans trafic mais
avec 40 backlinks vaut plus qu'une page à 200 visites/mois.

Sortie : `inventaire.csv` avec par URL — impressions, clics, position
moyenne, backlinks, domaines référents, valeur estimée.

## Phase 2 — Mapping des redirections

Une ligne par ancienne URL. **Aucune exception.**

| Ancienne URL | Nouvelle URL | Type | Justification |
|---|---|---|---|
| /services/plomberie | /prestations/plomberie | 301 | Équivalent direct |
| /blog/vieux-article | /blog/nouveau-guide | 301 | Contenu fusionné |
| /promo-2019 | — | 410 | Obsolète, aucun backlink, aucune impression |

Règles :
- **301**, jamais 302, pour une migration
- Toujours vers l'**équivalent le plus proche**, jamais vers la home. Une
  redirection massive vers la home est traitée comme un soft 404 : vous
  perdez tout le signal.
- Pas de chaîne : ancien → nouveau, directement
- Si aucun équivalent n'existe et que l'URL a de la valeur, **créez la page**
- Si l'URL n'a ni trafic ni backlink : 410, et c'est propre

Traitez d'abord les 20 % d'URL qui portent 80 % de la valeur, mais **couvrez
les 100 %**. Les longues traînes cumulées font souvent 30 % du trafic.

## Phase 3 — Checklist avant mise en ligne

- [ ] Plan de redirections complet et testé sur la préproduction
- [ ] `noindex` retiré de la préprod (l'oubli le plus coûteux du métier)
- [ ] robots.txt de production, pas celui de préprod
- [ ] Canonicals auto-référentes sur les nouvelles URL
- [ ] Titles et metas repris ou améliorés — jamais perdus
- [ ] Contenu réellement transféré : comparez le nombre de mots par page
- [ ] Données structurées reportées
- [ ] Hreflang mis à jour si multilingue
- [ ] Nouveau sitemap prêt
- [ ] GA4 et GSC configurés sur la nouvelle propriété
- [ ] Redirections HTTP→HTTPS et www→non-www (ou l'inverse) cohérentes
- [ ] Performance de la nouvelle version mesurée (un site plus lent perd)
- [ ] Sauvegarde complète de l'ancien site, fichiers et base

## Phase 4 — Le jour J

1. Mise en ligne
2. **Tester 30 redirections au hasard** dans les 15 minutes, dont les 10
   URL les plus importantes
3. Soumettre le nouveau sitemap dans Search Console
4. Si changement de domaine : outil « Changement d'adresse » dans GSC
5. Garder l'ancien sitemap soumis 30 jours — il aide Google à découvrir les
   redirections plus vite
6. Vérifier le robots.txt en production, à la main
7. Inspection d'URL sur 5 pages clés

## Phase 5 — Surveillance

| Échéance | À vérifier | Normal |
|----------|-----------|--------|
| J+1 | Erreurs 404, crawl, robots.txt | Quelques 404 résiduels |
| J+7 | Couverture GSC, positions top 20 | Baisse de 10-20 % |
| J+30 | Trafic organique | Retour à ~90 % |
| J+90 | Trafic organique | Retour à 100 % ou plus |

**Une baisse de 10-20 % pendant 2-4 semaines est normale.** Ne paniquez pas,
ne changez rien pendant cette fenêtre : la réaction précipitée aggrave
presque toujours la situation.

Au-delà de J+60 sans reprise, cherchez dans cet ordre :
1. Redirections manquantes ou en boucle (le plus fréquent)
2. Contenu réellement perdu à la refonte
3. Maillage interne appauvri par le nouveau design
4. Performance dégradée
5. `noindex` oublié quelque part

## Réparer une migration déjà ratée

1. Récupérer la liste des anciennes URL via GSC (16 mois) et l'Internet
   Archive si nécessaire
2. Tester chacune : où atterrit-elle aujourd'hui ?
3. Toute URL qui finit en 404 ou sur la home et qui avait du trafic ou des
   backlinks → redirection correcte immédiate
4. Comparer le contenu d'avant (cache, Archive) et d'après sur les 20 pages
   les plus importantes : ce qui a été perdu doit être remis
5. Resoumettre le sitemap

Le trafic revient rarement à 100 % après une migration ratée corrigée
tardivement. Visez 80-90 % et travaillez le reste en création.

## Livrables

- `INVENTAIRE.csv` — l'ancien site avec sa valeur par URL
- `REDIRECTIONS.csv` — le mapping complet
- `redirections.conf` / `.htaccess` / règles CMS — prêtes à poser
- `CHECKLIST-MIGRATION.md` — cochable
- `SURVEILLANCE.md` — le protocole J+1 à J+90
