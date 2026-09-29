# Dépannage

## Les MCP

| Symptôme | Cause | Correctif |
|----------|-------|-----------|
| Un MCP n'apparaît pas | Node absent, ou Claude non redémarré | `node -v`, puis relancer Claude Code |
| Tous les MCP absents | `.mcp.json` mal placé | Il doit être à la racine du projet |
| Un MCP démarre puis meurt | Variable d'environnement vide | `/seo doctor` pour voir laquelle |

## Search Console

| Symptôme | Cause | Correctif |
|----------|-------|-----------|
| 403 Forbidden | Le compte de service n'est pas dans Search Console | L'ajouter en lecture seule dans Paramètres → Utilisateurs |
| 0 ligne renvoyée | Mauvais format de propriété | Essayer `sc-domain:exemple.com` |
| 401 | Fichier JSON introuvable ou invalide | Vérifier le chemin dans `GSC_CREDENTIALS_JSON` |
| Données incomplètes | Latence normale de l'API | 2-3 jours de retard, c'est attendu |
| Pas d'historique ancien | Limite de l'API | 16 mois maximum, c'est une limite Google |

## Google Analytics 4

| Symptôme | Correctif |
|----------|-----------|
| 403 | Ajouter le compte de service en Lecteur sur la propriété GA4 |
| Propriété introuvable | `GA4_PROPERTY_ID` doit être le nombre à 9 chiffres, pas l'ID de flux |

## DataForSEO

| Symptôme | Correctif |
|----------|-----------|
| 401 | Les identifiants API ne sont pas ceux du site. Les récupérer dans **API Access** |
| Réponses vides | Vérifier le code pays et la langue dans la requête |

## WordPress

| Symptôme | Cause | Correctif |
|----------|-------|-----------|
| 401 | Mot de passe de compte au lieu du mot de passe d'application | En générer un dans Utilisateurs → Profil |
| 403 | L'API REST est bloquée | Plugin de sécurité ou règle serveur : autoriser `/wp-json/` |
| Le contenu passe, pas les balises SEO | Champs meta non exposés dans l'API | Dépend du plugin — voir la doc de Yoast / Rank Math / SEOPress |
| Le HTML est modifié à la publication | Filtres WordPress (`wpautop`) | Vérifier le rendu, ajuster le balisage |

## Webflow

| Symptôme | Correctif |
|----------|-----------|
| Champ refusé | Le slug de champ doit correspondre exactement à celui de la Collection |
| Modification invisible sur le site | La création ne publie pas — publier le site est une étape séparée |
| Embed tronqué | Limite de 50 000 caractères, découper le bloc |

## Notion

| Symptôme | Cause | Correctif |
|----------|-------|-----------|
| « object not found » avec un token valide | La page n'est pas partagée avec l'intégration | Sur la page → ••• → Connexions → ajouter l'intégration |
| Impossible de créer une base | Capacité d'insertion non accordée | Vérifier les capacités de l'intégration |

## Chrome DevTools

| Symptôme | Correctif |
|----------|-----------|
| Ne rend rien | Chrome ou Chromium absent — l'installer |
| Timeout sur les pages lourdes | Normal, réessayer ou augmenter le délai |
| Mesures très différentes de PageSpeed | Normal : labo vs terrain. Le terrain fait foi |

## Scripts Python

| Symptôme | Correctif |
|----------|-----------|
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| Crawl très lent | Normal : 1 requête/seconde par politesse. `--delai 500` pour accélérer |
| Le crawl s'arrête tôt | Limite `--max`, ou blocage robots.txt |

## Les garde-fous

| Symptôme | Explication |
|----------|-------------|
| « BLOQUE : aucun domaine autorisé » | Renseignez `GSC_SITE_URL` ou `SEO_ALLOWED_DOMAINS` dans `.env` |
| « BLOQUE : mode safe actif » | `SEO_SAFE_MODE=1`, ou `--safe`, ou `mode: safe` dans la config |
| « BLOQUE : 800 pages » | Seuil de sécurité. Auditez un échantillon de 20 pages d'abord |
| Reddit refuse de publier | Garde-fou non désactivable. Publiez à la main |

---

Un problème qui n'est pas ici ?
[Ouvrez une issue](https://github.com/NathanFenina/decupler-seo/issues) avec la
sortie de `/seo doctor`.
