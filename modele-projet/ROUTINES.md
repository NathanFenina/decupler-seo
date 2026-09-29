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

## 1 · Veille — tous les jours, 7 h 07

```
Tu es le SEO manager de ce projet. Lis CLAUDE.md.
Lance le skill seo-cycle en mode veille.
N'écris rien sur le site. Si tout va bien, termine sans rien produire
d'autre que le journal de run. S'il y a une anomalie, décris-la dans
rapports/a-valider.md avec quoi, depuis quand, combien ça coûte, quoi faire.
Commite et pousse sur une branche claude/veille-<date>.
```

## 2 · Optimisation — le lundi, 7 h 17

```
Tu es le SEO manager de ce projet. Lis CLAUDE.md.
Lance le skill seo-cycle en mode optimisation.
Respecte strictement les niveaux d'autonomie de CLAUDE.md et les plafonds de
decupler-seo.config.yml. Journalise chaque modification publiée avec
seo-journal-mesure AVANT de passer à la suivante.
Commite et pousse sur une branche claude/optimisation-<date>.
```

## 3 · Contenu — le mercredi, 7 h 17

```
Tu es le SEO manager de ce projet. Lis CLAUDE.md.
Lance le skill seo-cycle en mode contenu.
Produis au plus le nombre de pages neuves autorisé par semaine, publiées
selon publication.mode de la config (brouillon CMS, ou pull request sur un
site en code), et liste-les dans rapports/a-valider.md.
Commite et pousse sur une branche claude/contenu-<date>.
```

## 4 · Rapport — le 1er du mois, 7 h 27

```
Tu es le SEO manager de ce projet. Lis CLAUDE.md.
Lance le skill seo-cycle en mode rapport : mesure toutes les modifications
arrivées à échéance (seo-journal-mesure), mets à jour
memoire/apprentissages.md, relève la cartographie du mois
(cartographie.py mensuel → rapports/cartographie-<AAAA-MM>.md), puis écris
rapports/<AAAA-MM>.md et rapports/<AAAA-MM>.json. Vérifie aussi rapports/runs/ : signale toute
routine qui n'a pas produit son journal de run ce mois-ci.
Commite et pousse sur une branche claude/rapport-<date>.
```

## Pourquoi un journal de run

Un statut vert dans la liste des routines veut dire que la session a démarré
et s'est terminée sans erreur d'infrastructure, **pas** que le travail a été
fait. Chaque exécution écrit donc `rapports/runs/<date>-<mode>.md`, et la
routine de rapport vérifie qu'aucune n'a manqué.

## Votre temps : 30 minutes le lundi

1. Lire `rapports/a-valider.md`
2. Valider ou refuser, et consigner dans `memoire/decisions.md`
3. Fusionner les branches `claude/` que vous acceptez
