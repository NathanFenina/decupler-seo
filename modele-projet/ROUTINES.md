# Les routines de {{NOM}}

Quatre routines font tourner ce projet en autonomie. Créez-les sur
https://claude.ai/code/routines → **New routine** → **Cloud**.

## Réglages communs aux quatre

- **Dépôt** : ce dépôt uniquement. Une routine à un seul dépôt lit son
  `CLAUDE.md`, ses skills, ses agents et son `.mcp.json`.
- **Connecteurs** : gardez seulement ceux dont la routine a besoin
  (Search Console via Windsor.ai ou équivalent, le CMS, Notion si utilisé).
  Une routine peut utiliser **toutes** les actions d'un connecteur inclus,
  y compris les écritures, sans demander.
- **Environnement** : créez-en un dédié au projet.
  - **Réseau** : *Custom*, avec `{{DOMAINE_NU}}` dans les domaines autorisés
    et la liste par défaut cochée. Sans ça, toute lecture du site échoue en 403.
  - **Clés** : en *API credentials* sur Pro/Max, en variables d'environnement
    sur Team. Jamais dans le dépôt.
  - **Search Console** (mesure automatique, sans connecteur) : variables
    `GSC_SA_JSON` (contenu de la clé du compte de service, JSON brut ou
    base64 — compte en lecture seule sur la propriété) et `GSC_SITE_URL`
    (`sc-domain:exemple.com` ou `https://www.exemple.com/`, exactement comme
    dans Search Console). Autorisez aussi `oauth2.googleapis.com` et
    `www.googleapis.com` dans le réseau. Test :
    `python3 .claude/decupler-seo/scripts/gsc.py sites`.
- **Heure** : quelques minutes après l'heure pile (7 h 07 et non 7 h 00),
  sinon le départ peut glisser de plusieurs minutes.

## Le prompt de chaque routine : court, il renvoie au dépôt

Les consignes vivent dans `routines/<mode>.md`, versionnées avec le projet.
Le prompt de la routine ne fait que les lire :

```
Routine de <mode> de {{NOM}}. Commence par `git fetch origin main`, puis lis
les instructions à jour avec `git show origin/main:routines/<mode>.md` et
suis-les à la lettre, étape par étape.
```

Pourquoi : le prompt d'une routine ne se modifie que depuis la conversation
qui l'a créée. Avec ce prompt court, améliorer une routine revient à modifier
un fichier du dépôt, depuis n'importe quelle conversation, sans la recréer.

| Routine | `<mode>` | Quand (Europe/Paris) |
|---|---|---|
| Veille | `veille` | tous les jours, 7 h 07 |
| Optimisation | `optimisation` | le lundi, 7 h 17 |
| Contenu | `contenu` | le mercredi, 7 h 17 |
| Rapport et roadmap | `rapport` | le 1er du mois, 7 h 27 |

Sur plusieurs projets, décalez les heures de 5 minutes d'un projet à l'autre,
et l'optimisation d'un jour par rapport à toute autre routine qui écrit les
mêmes fichiers.

## Pourquoi un journal de run

Un statut vert dans la liste des routines veut dire que la session a démarré
et s'est terminée sans erreur d'infrastructure, **pas** que le travail a été
fait. Chaque exécution écrit donc `rapports/runs/<date>-<mode>.md`, et la
routine de rapport vérifie qu'aucune n'a manqué.

## Votre temps : 30 minutes le lundi

1. Ouvrir la page de suivi du projet : valider ou refuser les actions du mois
2. Lire `rapports/a-valider.md`, consigner les décisions dans `memoire/decisions.md`
3. Fusionner les PR marquées « à fusionner par un humain »
