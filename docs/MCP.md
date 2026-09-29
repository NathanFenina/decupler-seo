# Brancher les 13 MCP

Aucun n'est obligatoire. Les skills s'adaptent à ce qui est branché et vous
disent ce qui manque. Commencez par le niveau 1 : c'est gratuit et ça couvre
70 % de la valeur du dispositif.

À tout moment :
```
/seo doctor
```
vous dit qui répond, qui manque, et quoi brancher ensuite.

---

## Niveau 1 — Le socle gratuit

### Google Search Console

**Ce que ça débloque** : les quick wins, les rapports, le diagnostic de chute
de trafic, et toute la priorisation. Sans lui, vous devinez.

**Limite à connaître** : l'API ne remonte que **16 mois** d'historique. Pour
des comparaisons au-delà, il faut archiver vous-même.

#### Méthode A — Connecteur (5 min, aucun code)

Réglages Claude → Connecteurs → autoriser l'accès Google → sélectionner la
propriété Search Console. Pour qui ne veut pas voir un terminal.

#### Méthode B — Compte de service (10 min, scriptable)

1. [Google Cloud Console](https://console.cloud.google.com) → nouveau projet
2. **API et services** → activer **Search Console API**
3. **IAM et administration** → **Comptes de service** → créer
4. Sur le compte créé : **Clés** → Ajouter une clé → JSON → télécharger
5. Déposer le fichier dans `./secrets/gsc-service-account.json`
6. Dans **Search Console** → Paramètres → Utilisateurs et autorisations →
   ajouter l'email du compte de service **en lecture seule**
7. Dans `.env` :
   ```
   GSC_SITE_URL=https://votre-site.com/
   GSC_CREDENTIALS_JSON=./secrets/gsc-service-account.json
   ```

> ⚠️ Ne donnez **jamais** le rôle propriétaire à un compte de service.
> Lecture seule suffit pour tout ce que fait ce dispositif.

**Format de propriété** : si l'API renvoie 0 ligne, votre propriété est
probablement de type domaine. Essayez `sc-domain:exemple.com` au lieu de
`https://exemple.com/`.

---

### Google Analytics 4

**Ce que ça débloque** : les conversions organiques, la valeur business par
page. C'est ce qui permet de dire « cette page a rapporté 32 000 € » au lieu
de « cette page est en position 4 ».

1. Même projet Google Cloud → activer **Google Analytics Data API**
2. Réutiliser le même compte de service
3. Dans GA4 → Admin → Gestion des accès → ajouter l'email du compte de
   service en **Lecteur**
4. Récupérer l'ID de propriété (Admin → Paramètres de la propriété, un
   nombre à 9 chiffres)
5. Dans `.env` :
   ```
   GA4_PROPERTY_ID=123456789
   GA4_CREDENTIALS_JSON=./secrets/ga4-service-account.json
   ```

---

### Chrome DevTools

**Ce que ça débloque** : les Core Web Vitals **mesurés** et non estimés, le
rendu final après JavaScript, les captures d'écran.

**Aucune clé.** Il faut juste Node et Chrome installés.

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--isolated"]
    }
  }
}
```

Déjà présent dans le `.mcp.json` du dépôt. Si le MCP ne répond pas :
`node -v` puis vérifiez que Chrome ou Chromium est installé.

---

## Niveau 2 — La donnée marché

### Firecrawl

**Ce que ça débloque** : lire les concurrents en markdown propre, JavaScript
rendu inclus. Sert dans les briefs, les quick wins, l'analyse de SERP.

Offre gratuite généreuse : [firecrawl.dev](https://firecrawl.dev) → clé API →
`FIRECRAWL_API_KEY` dans `.env`.

### DataForSEO

**Ce que ça débloque** : volumes de recherche, difficulté, SERP live,
positions des concurrents, présence d'AI Overview.

Le meilleur rapport qualité/prix du marché : paiement à la requête, pas
d'abonnement. Comptez quelques euros par mois en usage normal.

[app.dataforseo.com/api-access](https://app.dataforseo.com/api-access) →
`DATAFORSEO_USERNAME` et `DATAFORSEO_PASSWORD`.

> Ce ne sont **pas** vos identifiants de connexion au site : allez bien dans
> l'onglet API Access. C'est la cause n°1 des erreurs 401.

### Ubersuggest

**Ce que ça débloque** : expansion sémantique, suggestions Google, idées de
contenu.

Le plus simple : le **connecteur claude.ai** (Réglages → Connecteurs), un
clic, sans clé. Sinon `UBERSUGGEST_API_KEY`.

---

## Niveau 3 — Production et pilotage

### WordPress

**Ce que ça débloque** : publication automatique en brouillon, mise à jour de
pages existantes.

1. WordPress → **Utilisateurs** → votre profil
2. Section **Mots de passe d'application** → en générer un nommé « Claude »
3. Copier la valeur affichée (elle ne sera plus visible ensuite)
4. Dans `.env` :
   ```
   WP_SITE_URL=https://votre-site.com
   WP_USERNAME=votre_identifiant
   WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
   ```

> Jamais votre mot de passe de connexion. Un mot de passe d'application se
> révoque en un clic sans changer votre accès.

**Les balises SEO** dépendent de votre plugin (Yoast, Rank Math, SEOPress).
Elles doivent être exposées dans l'API REST — ce n'est pas toujours le cas
par défaut. Si l'écriture des titles échoue silencieusement, c'est ça.

### Webflow

Site settings → **Apps & integrations** → API access → Generate token.
```
WEBFLOW_TOKEN=...
WEBFLOW_SITE_ID=...
```

Le contenu vit dans des **CMS Collections** aux champs prédéfinis : on ne
peut écrire que dans les champs existants. La création ne publie pas — c'est
une étape séparée.

### Notion

**Ce que ça débloque** : les 5 bases de pilotage — leads, objectifs, roadmap,
contenus, backlinks.

**Recommandé** : le connecteur natif claude.ai (Réglages → Connecteurs →
Notion). Aucune clé.

Sinon : [notion.so/my-integrations](https://www.notion.so/my-integrations) →
New integration → capacités lecture + écriture + insertion →
`NOTION_TOKEN=secret_...`

> ⚠️ Dans les deux cas, il faut **partager explicitement la page** avec
> l'intégration : sur la page Notion → « ••• » → Connexions → ajouter.
> Sans ça, l'API renvoie « object not found » même avec un token valide.
> C'est 90 % des échecs de connexion Notion.

### Semrush et Ahrefs

Plans API requis, généralement sur les offres supérieures.
[semrush.com/api-analytics](https://www.semrush.com/api-analytics/) ·
[ahrefs.com/api](https://ahrefs.com/api)

Utiles pour les gaps concurrents (Semrush) et les backlinks (Ahrefs). Le
dispositif fonctionne sans, avec moins de données de marché.

---

## Niveau 4 — Visibilité IA

### Perplexity

**Ce que ça débloque** : la mesure automatisée de votre part de voix dans les
moteurs IA (`/seo share-of-model`).

[docs.perplexity.ai](https://docs.perplexity.ai) → clé API Sonar →
`PERPLEXITY_API_KEY`. Quelques euros par mois.

Sans la clé, le script prépare une grille de relevé manuel : la mesure reste
possible, elle est juste plus lente.

### Reddit

**Ce que ça débloque** : les questions réelles de votre audience, leur
vocabulaire, et les threads fortement cités par les LLM.

[reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) → create app →
type **script** →
```
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
```

---

## Connecteurs claude.ai vs MCP locaux

Deux façons de brancher un outil, selon votre profil :

| | Connecteur claude.ai | MCP local (`.mcp.json`) |
|---|---|---|
| Installation | Un clic dans les réglages | Un fichier de config |
| Clé API | Aucune (OAuth) | À obtenir soi-même |
| Disponible pour | Notion, Ubersuggest, Google (via connecteurs tiers)… | Tous |
| Scriptable | Non | Oui |
| Convient à | Une utilisation dans l'interface Claude | Claude Code, automatisation |

Les deux peuvent coexister. Prenez le connecteur quand il existe, le MCP
quand vous voulez automatiser.

---

## Vérifier

```
/seo doctor
```

Si un MCP n'apparaît pas dans Claude Code :
1. `node -v` — Node est-il installé ?
2. Avez-vous **redémarré Claude Code** après avoir modifié `.mcp.json` ?
3. Le fichier `.env` est-il bien à la racine du projet ?
4. Voir [docs/DEPANNAGE.md](DEPANNAGE.md)
