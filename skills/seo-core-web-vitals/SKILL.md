---
name: seo-core-web-vitals
description: >
  Mesure les Core Web Vitals réels (LCP, INP, CLS) via Chrome DevTools,
  identifie la cause exacte de chaque métrique dégradée et applique les
  correctifs front. Déclencher sur "Core Web Vitals", "CWV", "LCP", "INP",
  "CLS", "PageSpeed", "site lent", "performance", "temps de chargement",
  "vitesse", "Lighthouse", "mon site rame".
---

# Core Web Vitals — mesurer, comprendre, corriger

La performance ne fait pas ranker un mauvais contenu. Elle départage à
qualité égale, et elle décide de la conversion. Traitez-la comme telle :
après le contenu, jamais avant.

## Mesurer pour de vrai

Via le MCP Chrome DevTools, sur mobile **et** desktop, réseau bridé
(4G lente) — c'est la condition de la majorité de vos visiteurs.

Les données de labo (Lighthouse) diagnostiquent. Les données de terrain
(CrUX, rapport GSC Signaux web) décident. **Si les deux divergent, le
terrain a raison** : c'est ce que Google utilise.

## Les seuils

| Métrique | Bon | À améliorer | Mauvais |
|----------|-----|-------------|---------|
| **LCP** — affichage du plus grand élément | < 2,5 s | 2,5-4 s | > 4 s |
| **INP** — réactivité aux interactions | < 200 ms | 200-500 ms | > 500 ms |
| **CLS** — stabilité visuelle | < 0,1 | 0,1-0,25 | > 0,25 |

> INP a remplacé FID le 12 mars 2024, et FID a disparu de tous les outils
> Chrome le 9 septembre 2024. Toute recommandation mentionnant FID est
> périmée — ne le citez jamais.

Le seuil se juge au **75e percentile** : 75 % des visites doivent être
bonnes. Une moyenne correcte peut cacher un quart d'expériences désastreuses.

## LCP — décomposer avant de corriger

Le LCP se découpe en 4 sous-parties. Identifiez laquelle domine, sinon vous
optimisez au hasard :

| Sous-partie | Cible | Correctif |
|-------------|-------|-----------|
| TTFB (serveur) | < 800 ms | Cache, CDN, requêtes SQL, hébergement |
| Délai de chargement de la ressource | < 10 % | `preload` + `fetchpriority="high"` |
| Chargement de la ressource | < 40 % | Compresser, WebP/AVIF, dimensionner |
| Délai de rendu | < 10 % | Retirer le CSS/JS bloquant |

Correctifs appliqués automatiquement quand le code est accessible :

```html
<!-- Image LCP : jamais en lazy, toujours prioritaire -->
<img src="hero.webp" width="1200" height="630" fetchpriority="high" alt="…">

<!-- Préconnexion aux origines tierces critiques -->
<link rel="preconnect" href="https://cdn.exemple.com" crossorigin>

<!-- Polices : éviter le texte invisible -->
<link rel="preload" href="/police.woff2" as="font" type="font/woff2" crossorigin>
```
```css
@font-face { font-display: swap; }
```

Erreur la plus fréquente : `loading="lazy"` sur l'image du hero. Ça retarde
le LCP de plusieurs centaines de millisecondes. **Lazy uniquement sous la
ligne de flottaison.**

## INP — la tâche longue est le coupable

INP mesure le pire délai de réaction sur l'ensemble de la session. La cause
est presque toujours une **tâche JavaScript longue** qui bloque le thread
principal.

Correctifs :
- Découper les tâches > 50 ms (`scheduler.yield()`, ou `setTimeout` en repli)
- Différer tout le JS non essentiel au premier écran
- Retirer les scripts tiers non indispensables — un chat, un A/B testing et
  trois pixels marketing suffisent à faire exploser l'INP
- Éviter les gestionnaires d'événements coûteux (recalculs de layout)
- Virtualiser les listes longues

Mesurez avec le profileur de performance Chrome DevTools sur une interaction
réelle : clic sur le menu, ouverture d'un filtre, soumission de formulaire.

## CLS — presque toujours 4 causes

1. **Images sans dimensions** → ajouter `width` et `height` (ou `aspect-ratio`)
2. **Publicités / iframes sans conteneur réservé** → `min-height` sur le slot
3. **Polices web** → `size-adjust` ou `font-display: optional`
4. **Contenu injecté au-dessus de l'existant** (bandeau cookies, promo) →
   le réserver dans le flux, ou le positionner en overlay

Le CLS est la métrique la moins chère à corriger et celle qui échoue le plus
souvent. Commencez par elle.

## Priorisation

Ne corrigez pas tout le site. Ordre :
1. Le gabarit le plus vu (souvent la fiche produit ou l'article)
2. Les pages de conversion
3. La home

Un correctif de gabarit répare des milliers de pages d'un coup.

## Vérification

Re-mesurer après application. Puis surveiller le rapport Signaux web de
Search Console : le terrain met **28 jours** à refléter un correctif. Ne
concluez pas à l'échec avant.

## Livrables

- `CWV-RAPPORT.md` — mesures, causes, correctifs
- `patches/` — les diffs front
- `AVANT-APRES.md` — les chiffres, avant et après
