# Prise en main pas à pas

Deux parcours, à suivre dans l'ordre, sans rien sauter. Chaque étape dit
**quoi faire**, **ce que vous devez voir**, et **quoi faire si ça bloque**.
Cochez au fur et à mesure.

- **Parcours 1 · 15 minutes** : le plugin sur votre poste, un premier
  résultat sur votre site.
- **Parcours 2 · 1 heure** : votre premier projet piloté (un site, sa
  mémoire, sa routine du mercredi).

Vous êtes prestataire sur un projet existant ? Allez directement au
[Parcours 3](#parcours-3--rejoindre-un-projet-en-tant-que-prestataire).

---

## Parcours 1 · Le plugin, 15 minutes

### ☐ 1. Installer Claude Code

Suivez https://code.claude.com, puis ouvrez un terminal dans n'importe quel
dossier et tapez `claude`.

**Vous devez voir** : l'invite de Claude Code.
**Si ça bloque** : la page d'installation officielle couvre macOS, Windows et
Linux ; Python 3.9 ou plus et git doivent être installés.

### ☐ 2. Installer le plugin (2 commandes)

```
/plugin marketplace add NathanFenina/decupler-seo
/plugin install decupler-seo@decupler
```

**Vous devez voir** : « decupler-seo » dans `/plugin`, onglet Installed.
Activez au passage la mise à jour automatique : `/plugin` → Marketplaces →
`decupler` → auto-update.

### ☐ 3. Le diagnostic

```
/seo doctor
```

**Vous devez voir** un tableau de ce type :

```
Prérequis système
  ✓ python3    3.11
  ✓ git        présent
─── Niveau 1 · Socle gratuit — commencez par là
  ✓ Google Search Console
  ○ Google Analytics 4  (gratuit)
      débloque : Conversions organiques, valeur business par page, rapport mensuel complet
      obtenir  : Google Cloud → Analytics Data API → compte de service
```

`✓` = branché, `○` = à brancher, avec ce que ça débloque et comment
l'obtenir. Claude enchaîne sur la première action utile.

### ☐ 4. Brancher Search Console (le plus rentable)

Suivez la section Search Console de [MCP.md](MCP.md) : un compte de service
Google, ajouté en lecture sur votre propriété, et deux variables
(`GSC_SA_JSON`, `GSC_SITE_URL`) dans un fichier `.env` **jamais commité**.
Relancez `/seo doctor` : la ligne passe à `✓`.

### ☐ 5. Trois premiers résultats

Dites à Claude, l'un après l'autre :

1. « Quelles pages de mon site rattraper ce mois-ci ? » (`/seo quickwins`) :
   les pages en position 4 à 20, chiffrées, corrections écrites.
2. « Fais le brief de "<un mot-clé de votre métier>" » (`/seo brief`) : le
   top 5 lu, la réponse directe et la FAQ déjà rédigées.
3. « Audite <votre site> » (`/seo audit`) : score, plan priorisé.

**C'est fini.** Pour aller plus loin, chaque action a sa procédure :
[les SOP](sop/README.md). « Suis la SOP <nom> pour <sujet> » suffit.

---

## Parcours 2 · Votre premier projet, 1 heure

Un projet = un dépôt GitHub **privé** par site, qui contient la méthode, la
mémoire du site et sa routine. C'est ce qui permet à Claude de travailler
seul chaque semaine.

### ☐ 1. Créer le projet

Dans Claude Code : « nouveau projet pour <domaine> ». Claude pose ses
questions en une fois, puis lance :

```bash
python3 scripts/projet.py init ../client --nom "Client" --domaine https://www.client.fr
```

**Vous devez voir** :

```
  ✓ Projet « Client » créé dans …/client
  Méthode (aucune) → 3.9.1+…
  221 ajouté(s) · 0 mis à jour · 0 retiré(s) · 0 inchangé(s)
  ✓ Méthode synchronisée dans …/client/.claude
```

Un site qui a déjà son dépôt : `projet.py adopter` à la place de `init`,
rien d'existant n'est écrasé.

### ☐ 2. Donner sa voix au site (le plus important)

- Remplir `memoire/marque.md` : à qui on parle, ce qui les inquiète, les mots
  interdits, les chiffres officiels.
- « Mesure le style du site sur ces 5 pages : <URL> » (`style_maison.py`) :
  Claude écrit `memoire/style.md`. C'est ce qui rend les textes
  reconnaissables comme ceux du client, pas comme de l'IA.
- Chaque chiffre que le site pourra publier va dans `memoire/faits.md`, avec
  sa source et sa date. Aucun autre chiffre ne sortira.

### ☐ 3. Mettre le projet sur GitHub, en privé

```bash
cd ../client && git init && git add -A && git commit -m "Projet Client"
```

Créez le dépôt **privé** sur GitHub, poussez, puis dans le dépôt :
Settings › Actions › General › cocher « Allow GitHub Actions to create and
approve pull requests ». **Vous devez voir**, le lundi suivant, une PR
« Méthode decupler-seo <version> » si la méthode a évolué.

Dans Settings › Secrets and variables › Actions, ajoutez `GSC_SA_JSON`,
`GSC_SITE_URL` et `INDEXNOW_KEY` (`indexation.py cle` la crée) : l'action
« Indexation automatique » annonce chaque jour les pages publiées ou
modifiées.

### ☐ 4. Créer la routine du mercredi

Sur https://claude.ai/code/routines → New routine → Cloud, avec ce dépôt
seulement, le mercredi à 7 h 07 (décalez de 5 minutes d'un projet à l'autre),
et ce prompt, tel quel :

```
Routine hebdo de <Client>. Commence par `git fetch origin main`, puis lis les
instructions à jour avec `git show origin/main:routines/hebdo.md` et suis-les
à la lettre, étape par étape.
```

Détail des réglages (réseau, clés) : `ROUTINES.md` du projet.
**Vous devez voir**, le mercredi, une PR « hebdo » et un journal
`rapports/runs/<date>-hebdo.md`.

### ☐ 5. Votre semaine

- **Lundi, 10 minutes** : fusionner la PR de méthode s'il y en a une ;
  déposer les retours du client dans `notes/` avec `#a-traiter`.
- **Mercredi, 20 minutes** : lire la page de suivi, valider ou refuser ce qui
  est « À décider », lire `rapports/a-valider.md` (dont le constat
  d'indexation), fusionner ce qui attend un humain.

Le reste : [SOP 15 · La semaine type](sop/15-semaine-type.md) et
[SOP 16 · Arbitrer les actions](sop/16-arbitrer-les-actions.md).

### ☐ 6. Garder la méthode à jour, et l'améliorer

- « Mets à jour la méthode » (`/seo-maj`) dans le projet : statut, synchro
  sur une branche, PR.
- Vous avez amélioré un skill chez ce client et ça vaut pour tous ? « Remonte
  ça dans la méthode » (`projet.py remonter . --pousser`) : une PR sur
  decupler-seo, que tous les projets recevront.

---

## Parcours 3 · Rejoindre un projet en tant que prestataire

### ☐ 1. Recevoir les accès

Le dépôt (écriture, jamais sur `main`), le CMS en rôle éditeur, Search
Console en lecture. Les clés arrivent hors du dépôt : copiez `.env.example`
en `.env` et remplissez-le.

### ☐ 2. Ouvrir le projet

```bash
git clone <dépôt> && cd <dépôt> && claude
```

Puis `/seo doctor`. Pas de plugin à installer : la méthode est dans `.claude/`.

### ☐ 3. Lire avant de toucher à quoi que ce soit

Dans cet ordre : `Accueil.md`, `CLAUDE.md`, `memoire/marque.md`,
`memoire/style.md`, `memoire/decisions.md`. Ou dites : « Je suis prestataire
sur ce projet : lis la mémoire et résume-moi les règles. »

### ☐ 4. Une tâche = une branche = une PR

« Suis la SOP <nom> pour <tâche> », sur une branche
`presta/<prénom>-<tâche>`, puis ouvrez la PR. Détail :
[SOP 17](sop/17-travailler-avec-un-prestataire.md).

---

## Quand ça bloque

| Symptôme | Cause habituelle | Que faire |
|---|---|---|
| `/seo` inconnu | plugin pas installé ou pas rechargé | parcours 1, étape 2, puis redémarrer Claude Code |
| `sync` refuse : « fichier de méthode modifié localement » | quelqu'un a modifié `.claude/` à la main | `projet.py remonter .` si c'est une amélioration, sinon déplacer dans un skill `projet-…` |
| La routine est verte mais rien n'est fait | un statut vert = la session a tourné, pas le travail | lire `rapports/runs/<date>-hebdo.md` |
| Pas de PR de méthode le lundi | la case « Allow GitHub Actions… » n'est pas cochée | parcours 2, étape 3 |
| « Search Console non branchée » | variables absentes de l'environnement | `/seo doctor`, puis [MCP.md](MCP.md) |

Plus de cas : [DEPANNAGE.md](DEPANNAGE.md). Comment tout s'articule :
[MANUEL.md](MANUEL.md).
