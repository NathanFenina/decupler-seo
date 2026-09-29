# Sécurité et garde-fous

Ce dispositif écrit sur des sites en production. Ce document explique ce
qu'il peut faire, ce qu'il ne fera jamais, et comment l'arrêter.

---

## Les trois modes

| Mode | Comportement |
|------|--------------|
| `safe` | Aucune écriture externe. Tout sort en fichier local que vous posez vous-même. Zéro risque. |
| `assisted` | Écriture autorisée, mais chaque action est annoncée et attend un « oui ». |
| `autonomous` | Écriture directe, sans demander. Les garde-fous durs s'appliquent toujours. |

Se règle dans `./decupler-seo.config.yml`, à la racine de chaque projet.
Un projet créé par `projet.py init` ou `adopter` démarre en `assisted` :
passez-le en `autonomous` une fois les premières mesures bonnes. Sans
fichier de config dans le projet, c'est le modèle du plugin qui s'applique
(`autonomous`), et `doctor.py` le signale.
`SEO_SAFE_MODE=1` fonctionne aussi bien exporté dans le shell qu'écrit dans
le `.env` du projet.

---

## Le kill-switch

Trois façons d'arrêter, par ordre de priorité :

```bash
# 1 · Variable d'environnement — gagne sur tout le reste
export SEO_SAFE_MODE=1

# 2 · Flag sur une commande — gagne sur la config
/seo fix https://exemple.com --safe

# 3 · Config
mode: safe
```

Ou dites simplement à Claude : **« passe en safe mode »**.

Pour vérifier l'état courant :
```bash
python3 scripts/guard.py --statut
```

---

## Les garde-fous durs

Non désactivables, y compris en mode `autonomous`. Chacun correspond à une
façon connue de se faire mal.

### Jamais de suppression de contenu
Dépublier ou repasser en brouillon, oui. Supprimer, non — c'est irréversible
et ça casse les liens entrants.

### Jamais de post communautaire sans validation
Reddit, forums, Quora. Le dispositif rédige, **vous publiez**. Reddit détecte
et bannit les comptes automatisés, et le compte banni serait le vôtre. Un ban
sur un subreddit de votre secteur est définitif.

### Jamais d'email d'outreach sans validation
Le dispositif rédige les prises de contact, vous cliquez sur envoyer. Une
campagne automatisée détruit une réputation d'expéditeur en quelques jours,
et cette réputation vous appartient.

### Jamais d'écriture sur un domaine non déclaré
L'écriture externe est refusée tant qu'aucun domaine autorisé n'est
configuré. Renseignez `GSC_SITE_URL` ou `SEO_ALLOWED_DOMAINS` dans `.env`.

### Sauvegarde avant toute écriture
Chaque modification d'un contenu existant sauvegarde l'état d'origine dans
`.seo-decupler/backups/`. Restauration :
```bash
python3 scripts/cms_restore.py --lister
python3 scripts/cms_restore.py .seo-decupler/backups/<fichier>.json
```

### Une page en ligne ne change pas sans feu vert
Sur WordPress, `scripts/wp.py` crée les contenus neufs en brouillon et
envoie toute modification d'une page déjà publiée en **révision**
(autosave) : la page publique ne bouge pas tant que personne ne l'a validée
dans l'éditeur. La mise en ligne directe exige une demande explicite et le
verdict `AUTORISE` du garde-fou ; chaque modification mise en ligne est
journalisée avec sa valeur d'avant.

### Diff obligatoire sur les fichiers critiques
robots.txt, redirections, canonicals : le diff est toujours présenté avant
application, même en mode autonomous. Une règle `Disallow: /` posée par
erreur désindexe un site en 48 heures.

### Seuils de volume
| Action | Alerte | Blocage |
|--------|--------|---------|
| Pages programmatiques | 100 | **500** sans audit qualité |
| Pages locales | 30 | **50** (risque de doorway pages) |

### Contrôle des contenus, bloquant
`scripts/controle_contenu.py` passe avant toute publication, dans les deux
modes (`cms` et `depot`). Il renvoie une erreur, et la publication s'arrête,
sur un texte provisoire oublié, une promesse ou une preuve invérifiable
(« n°1 », « résultats garantis », compteur de clients), un interdit propre
au client (`regles.interdits`), un title ou une meta trop longs, plusieurs
H1, une image sans alt. Une consigne s'oublie dans une longue session ; un
code retour non nul, non.

### Sur un site en code, une fusion est une mise en ligne
En mode `depot`, le cycle travaille sur une branche et ouvre une pull
request. Il ne fusionne qu'en mode `autonomous`, contrôles tous verts.
Protégez la branche principale sur GitHub (contrôles requis avant fusion) :
c'est le garde-fou qui tient même si tout le reste est mal configuré.

### Jamais de chiffre inventé
Si une donnée n'est pas disponible, le dispositif écrit « donnée
indisponible — nécessite tel outil » et poursuit. Il ne comble pas les trous.

---

## Vos secrets

- `.env` et `secrets/` sont dans `.gitignore`. **Vérifiez avant de commiter.**
- Utilisez des **mots de passe d'application** (WordPress), jamais votre mot
  de passe de connexion.
- Les comptes de service Google doivent être en **lecture seule**. Jamais
  propriétaire.
- Révoquez ce que vous n'utilisez plus.

Si vous avez commité une clé par erreur : révoquez-la immédiatement chez le
fournisseur. Réécrire l'historique Git ne suffit pas — considérez-la comme
compromise.

---

## Ce que le dispositif fait avec vos données

- Il lit vos données Search Console, GA4, CMS.
- Il écrit dans `seo-output/` en local, et sur votre CMS si vous l'autorisez.
- Il envoie des requêtes aux API que **vous** avez configurées.
- Il ne transmet rien à Décupler. Ce dépôt n'a pas de télémétrie.

---

## En cas de problème

| Symptôme | Réaction |
|----------|----------|
| Une modification non voulue est partie | `python3 scripts/cms_restore.py --lister` puis restaurez |
| Vous voulez tout arrêter maintenant | `export SEO_SAFE_MODE=1` |
| Le site a été désindexé | Vérifiez robots.txt et les meta robots. Le diff de la modification est dans le journal de session |
| Une clé a fuité | Révoquez-la chez le fournisseur, immédiatement |
