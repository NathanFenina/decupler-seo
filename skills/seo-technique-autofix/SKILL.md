---
name: seo-technique-autofix
description: >
  Audit technique SEO ET application automatique des correctifs : robots.txt,
  sitemaps, canonicals, redirections, balises, hreflang, headers, données
  structurées, images. Détecte, génère le patch, l'applique dans le repo ou
  le CMS, et vérifie que c'est corrigé. Déclencher sur "corrige la technique",
  "fix SEO", "répare", "problèmes techniques", "robots.txt", "canonical",
  "redirections", "404", "chaînes de redirection", "audit technique",
  "erreurs d'indexation", ou après un audit qui a remonté des points techniques.
---

# Technique + correction automatique

La plupart des audits techniques finissent dans un PDF que personne
n'applique. Celui-ci applique. C'est toute la différence.

## Étape 0 — Vérifier le droit d'écrire

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/guard.py" --action modifier-robots --cible <url>
```

- `AUTORISE` → on corrige directement
- `DEMANDE_VALIDATION` → on présente le diff, on attend le oui
- `BLOQUE` → on produit les patchs en local, l'utilisateur les applique

Sur les fichiers critiques (robots.txt, redirections, canonicals), **on
montre toujours le diff avant**, même en mode autonomous. Une règle
`Disallow: /` posée par erreur désindexe un site en 48 h.

## Les 10 catégories, et le correctif de chacune

### 1. Crawlabilité
| Détection | Correctif appliqué |
|-----------|--------------------|
| robots.txt absent | Générer un robots.txt minimal + lien sitemap |
| `Disallow` bloquant une page à trafic | Retirer la règle, diff obligatoire |
| Sitemap absent des robots | Ajouter la directive `Sitemap:` |
| Pièges à crawl (facettes infinies) | Règles `Disallow` ciblées + `noindex` |
| Budget de crawl gaspillé sur des paramètres | Canonical + règles paramètres |

### 2. Indexabilité
`noindex` sur une page qui reçoit des impressions → **critique**, à retirer.
Vérifiez les trois emplacements possibles : meta robots, header
`X-Robots-Tag`, et le fichier robots.txt. Un `noindex` en header est le
plus souvent oublié parce qu'il n'apparaît pas dans le HTML.

### 3. Canonicals
- Canonical absente sur page indexable → l'ajouter, auto-référente
- Canonical vers une URL en 3xx ou 4xx → pointer vers la destination finale
- Canonical relative → passer en absolue
- Canonical en boucle ou croisée → démêler, la page la plus complète gagne
- Canonical HTTP sur site HTTPS → corriger le protocole

### 4. Redirections
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_redirects.py" <url> --suivre-chaines
```
- Chaîne de plus de 2 sauts → aplatir vers la destination finale
- 302 permanente déguisée → passer en 301
- Boucle → casser, choisir une destination
- 404 recevant des backlinks → **la plus grosse perte silencieuse.**
  Rediriger en 301 vers l'équivalent le plus proche, jamais vers la home
  (Google traite une redirection massive vers la home comme un soft 404).

### 5. Balises
| Problème | Règle appliquée |
|----------|-----------------|
| Title absent, dupliqué, > 60 car. | Réécrire, mot-clé dans les 3 premiers mots |
| Meta description absente ou > 160 car. | Réécrire, 150-160 car., promesse + différenciation |
| H1 absent ou multiple | Un seul H1, alignés sur l'intention |
| Hiérarchie Hn cassée (H2 → H4) | Rétablir la séquence |

### 6. HTTPS et sécurité
Mixed content, HSTS absent, certificat proche de l'expiration,
`X-Content-Type-Options`, `Referrer-Policy`. Le mixed content casse le
cadenas et fait fuir les utilisateurs avant même le SEO.

### 7. Structure d'URL
Majuscules, underscores, paramètres de session, profondeur > 4 clics,
absence de trailing slash cohérente. Attention : **renommer une URL qui
ranke coûte plus cher que la garder moche.** Ne corrigez que sur les URL
neuves ou sans historique, sinon signalez sans appliquer.

### 8. Mobile
Viewport absent, cibles tactiles < 48 px, texte < 16 px, contenu masqué en
mobile, interstitiels intrusifs. L'index est mobile-first : ce qui n'est pas
dans le rendu mobile n'existe pas pour Google.

### 9. Core Web Vitals
Mesure réelle via Chrome DevTools MCP, jamais estimée.
Seuils : LCP < 2,5 s · INP < 200 ms · CLS < 0,1.

> INP a remplacé FID le 12 mars 2024. FID a été entièrement retiré des
> outils Chrome le 9 septembre 2024. Ne mentionnez jamais FID.

Correctifs appliqués automatiquement quand le code est accessible :
`loading="lazy"` hors du viewport, `width`/`height` sur les images (CLS),
`fetchpriority="high"` sur l'image LCP, `preconnect` sur les origines
tierces, `font-display: swap`, différer les scripts non critiques.

### 10. Rendu JavaScript
Comparer le HTML brut et le DOM rendu. Si le contenu principal n'existe
qu'après exécution JS, signalez-le : Google le voit avec du retard et les
crawlers des LLM ne le voient pas du tout. C'est souvent LE problème de
fond d'un site qui « ne ranke pas sans raison ».

## Gestion des crawlers IA

Ne bloquez pas les crawlers IA par réflexe. Décision à prendre consciemment :

| Agent | Rôle | Recommandation |
|-------|------|----------------|
| `GPTBot` | Entraînement OpenAI | Bloquer = disparaître des réponses ChatGPT |
| `OAI-SearchBot` | Recherche ChatGPT | **Ne jamais bloquer** si vous voulez du trafic |
| `ChatGPT-User` | Navigation à la demande | Laisser passer |
| `PerplexityBot` | Index Perplexity | Laisser passer |
| `ClaudeBot` | Anthropic | Au choix |
| `Google-Extended` | Gemini / AI Overviews | Bloquer n'affecte pas le ranking Google classique |
| `CCBot` | Common Crawl | Alimente de nombreux modèles |

Bloquer l'entraînement tout en restant citable dans les réponses est une
position défendable — et c'est exactement ce que permet la distinction
`GPTBot` / `OAI-SearchBot`.

## Application

**Repo accessible** → modifier les fichiers, un commit par catégorie, message
explicite. Jamais de commit fourre-tout : si une correction casse quelque
chose, il faut pouvoir la révoquer seule.

**CMS branché** → API REST, sauvegarde de l'état d'origine dans
`.seo-decupler/backups/` avant toute écriture.

**Ni l'un ni l'autre** → produire les patchs prêts à coller, avec pour
chacun : où le poser, quoi remplacer, comment vérifier.

## Vérification (l'étape que tout le monde saute)

Après application, **re-tester**. Un correctif non vérifié n'est pas un
correctif. Reprenez la page, confirmez que le problème a disparu, et listez
dans le rapport final ce qui est corrigé / ce qui a échoué / ce qui reste
manuel.

## Livrables

- `TECHNIQUE-RAPPORT.md` — constats, sévérité, statut
- `CORRECTIFS-APPLIQUES.md` — le journal de ce qui a été touché
- `patches/` — les diffs, si non appliqués
- `ROLLBACK.md` — comment tout annuler
