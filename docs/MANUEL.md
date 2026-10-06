# Manuel — prendre en main decupler-seo

Ce dépôt est **une seule source de savoir SEO et GEO** : les procédures
(SOP), les skills qui les exécutent, les scripts qui mesurent, et le
gabarit d'un projet client. On l'utilise de trois façons. Trouvez la vôtre,
suivez ses étapes dans l'ordre, et vous n'avez rien d'autre à lire pour
commencer.

**Première fois ?** Suivez d'abord la [prise en main pas à pas](PRISE-EN-MAIN.md) :
chaque étape y dit ce que vous devez voir et quoi faire si ça bloque.

| Vous êtes | Votre chemin | Temps |
|---|---|---|
| Vous découvrez, vous voulez l'essayer sur votre site | [A. Essayer](#a-essayer-le-plugin-sur-votre-site) | 10 minutes |
| Prestataire sur un projet qui l'utilise déjà | [B. Rejoindre un projet](#b-rejoindre-un-projet-existant) | 30 minutes |
| Consultant ou agence, plusieurs sites à piloter | [C. Piloter des projets](#c-piloter-des-projets-en-autonomie) | une demi-journée par projet |

---

## Comment ça marche, en deux minutes

**Trois couches**, et chacune a un propriétaire :

| Couche | Ce que c'est | Où | Qui la modifie |
|---|---|---|---|
| **La méthode** | les SOP (quoi faire, dans quel ordre), les skills (comment le faire), les agents (qui le fait), les scripts (ce qui mesure et publie) | ce dépôt, `decupler-seo` | une PR ici, jamais une copie |
| **Le projet** | un site client : sa mémoire (marque, style, faits, décisions), son journal, ses données, ses skills `projet-…` | un dépôt privé par client | vous, vos prestataires, la routine |
| **Les outils** | Search Console, GA4, le CMS, Notion, DataForSEO… branchés par MCP ou par clé | `.mcp.json` du projet + variables d'environnement | vous, une fois |

**Comment une tâche se déroule.** Vous dites « suis la SOP brief pour "audit
geo" ». Claude lit la SOP, qui cite un skill ; le skill dit quoi faire et
appelle des scripts ; les scripts interrogent les outils et écrivent dans le
projet ; la mémoire du projet (marque, style, faits) rend le résultat propre à
ce client ; le journal garde la trace pour mesurer à J+28.

**Comment un projet avance seul.** Une routine, le mercredi, lit
`routines/hebdo.md` dans le dépôt : contrôle, chiffres, actions validées,
notes, bilan sur la page de suivi. Vous validez en 20 minutes (SOP 15).

**Pourquoi la méthode est copiée dans chaque projet.** Une routine tourne dans
une session cloud qui ne charge pas les plugins : elle ne voit que ce qui est
dans le dépôt qu'elle clone. La copie est tenue à jour par une PR chaque lundi,
et protégée : une modification à la main bloque la synchro jusqu'à ce qu'on
l'ait remontée ou déplacée.

---

## A. Essayer le plugin sur votre site

1. Installer Claude Code (https://code.claude.com), puis, dans une session :
   ```
   /plugin marketplace add NathanFenina/decupler-seo
   /plugin install decupler-seo@decupler
   ```
2. `/seo doctor` : ce qui est branché, ce qui manque, et la première action utile.
3. Brancher Search Console (le plus rentable) : [docs/MCP.md](MCP.md).
4. Essayer trois commandes : `/seo audit <votre site>`, `/seo quickwins`,
   `/seo brief "<un mot-clé>"`.
5. Lire les SOP dans l'ordre où vous en avez besoin : [docs/sop/](sop/README.md).

Mises à jour du plugin : `/plugin` → Marketplaces → `decupler` → activer la
mise à jour automatique, ou `claude plugin update decupler-seo@decupler`.

## B. Rejoindre un projet existant

Le projet est un dépôt privé : la méthode est déjà dedans (`.claude/`), vous
n'installez pas le plugin.

1. Recevoir l'accès au dépôt, au CMS (rôle éditeur) et à Search Console
   (lecture). Les clés arrivent hors du dépôt : mettez-les dans votre `.env`
   (modèle : `.env.example`).
2. `git clone`, ouvrir Claude Code dans le dossier, `/seo doctor`.
3. Lire, dans cet ordre : `Accueil.md`, `CLAUDE.md`, `memoire/marque.md`,
   `memoire/style.md`, `memoire/decisions.md`.
4. Suivre la [SOP 17 · Travailler avec un prestataire](sop/17-travailler-avec-un-prestataire.md) :
   une tâche = une action validée de la page de suivi = une branche = une PR.
5. Pour chaque tâche, sa SOP : « suis la SOP <nom> pour <sujet> ».

## C. Piloter des projets en autonomie

1. Installer le plugin (chemin A), puis créer le projet :
   « nouveau projet » dans Claude Code, ou
   `python3 scripts/projet.py init ../client --nom "Client" --domaine https://client.fr`.
   Dépôt déjà existant : `projet.py adopter`.
2. Remplir `memoire/marque.md` et lancer `style_maison.py` sur 5 à 10 pages du
   client : c'est ce qui rend les textes reconnaissables comme les siens.
3. Pousser le dépôt en **privé**, activer « Allow GitHub Actions to create and
   approve pull requests » (Settings › Actions › General) pour la mise à jour
   automatique de la méthode.
4. Créer **une** routine, le mercredi : [modele-projet/ROUTINES.md](../modele-projet/ROUTINES.md).
5. Ajouter le dépôt à `projets.json` ; `projet.py registre` montre l'état de
   tous les projets.
6. Votre semaine : [SOP 15 · La semaine type](sop/15-semaine-type.md). Vos
   choix du mois : [SOP 16 · Arbitrer les actions](sop/16-arbitrer-les-actions.md).

Optionnel : ouvrir le dépôt comme coffre Obsidian pour lire et annoter la
mémoire ([docs/PROJETS.md](PROJETS.md#obsidian)).

## Tutos pas à pas

Chaque tuto donne la phrase à dire à Claude et, à côté, la commande qu'il
lance. Les deux marchent.

### 1. Mettre à jour la méthode dans un projet

> « Mets à jour la méthode. » (ou `/seo-maj`)

```bash
python3 .claude/decupler-seo/scripts/projet.py statut .     # où on en est
git checkout -b methode/decupler-seo-<version>
python3 .claude/decupler-seo/scripts/projet.py sync .       # la méthode
python3 .claude/decupler-seo/scripts/projet.py completer .  # nouveautés du gabarit
git add -A && git commit -m "Méthode decupler-seo <version>" && git push -u origin HEAD
```

Puis ouvrir la PR et la fusionner. Si `sync` refuse parce qu'un fichier de
méthode a été modifié ici : tuto 2 d'abord.

### 2. Faire remonter une amélioration trouvée chez un client

> « Ce que tu viens de corriger dans le skill, remonte-le dans la méthode. »

```bash
python3 .claude/decupler-seo/scripts/projet.py remonter . --simuler   # voir ce qui partirait
python3 .claude/decupler-seo/scripts/projet.py remonter . .claude/skills/seo-brief/SKILL.md --pousser
```

Une branche `remontee/<projet>-<date>` arrive sur decupler-seo : ouvrir la PR,
retirer tout ce qui est propre au client (nom, domaine, chiffres), fusionner.
Le lundi suivant, tous les projets la reçoivent. Ce qui ne vaut que pour ce
client va dans `memoire/` ou dans un skill `.claude/skills/projet-…`.

### 3. Mettre à jour le plugin sur votre poste

```bash
claude plugin marketplace update decupler
claude plugin update decupler-seo@decupler
```

Redémarrer Claude Code. Pour ne plus y penser : `/plugin` → Marketplaces →
`decupler` → mise à jour automatique.

### 4. Ajouter un projet

> « Nouveau projet pour client.fr. »

```bash
python3 scripts/projet.py init ../client --nom "Client" --domaine https://client.fr   # nouveau dépôt
python3 scripts/projet.py adopter ../site-existant --nom "Site" --domaine https://site.fr   # dépôt existant
```

Puis : dépôt **privé** sur GitHub, une ligne dans `projets.json`, la routine du
mercredi (`ROUTINES.md`), et « Allow GitHub Actions to create and approve pull
requests » dans les réglages du dépôt.

### 5. Confier une tâche à un prestataire

Créer l'action sur la page de suivi, la valider, et lui envoyer :
> « Clone <dépôt>, lis Accueil.md, puis suis la SOP <nom> pour <sujet>. Une
> branche presta/<prénom>-<tâche>, une PR. »

Le reste est dans la [SOP 17](sop/17-travailler-avec-un-prestataire.md).

### 6. Savoir où en sont tous les projets

```bash
python3 scripts/projet.py registre    # depuis decupler-seo
```

Version de la méthode dans chaque projet, synchro automatique présente ou non,
ce qui est à synchroniser.

---

## Comment le savoir circule

```
            decupler-seo (ce dépôt, public)
     SOP · skills · agents · scripts · gabarit
        │                          ▲
        │ sync (PR du lundi)       │ remonter (PR vers decupler-seo)
        ▼                          │
   projet client A    projet client B    projet client C      (dépôts privés)
   mémoire · notes · journal · skills projet-*
```

- Vers le bas : `projet.py sync`, automatique chaque lundi par une PR dans
  chaque projet. Rien n'arrive sans validation.
- Vers le haut : une amélioration trouvée sur un client
  (`projet.py remonter . --pousser`) devient une PR sur decupler-seo. Une
  fois fusionnée, tous les projets la reçoivent.
- Ce qui ne vaut que pour un client reste dans son projet : `memoire/` et
  skills `projet-…`. Jamais deux versions d'un même skill.

Tout en une commande, depuis un projet : `/seo-maj`.

## Les règles qui ne bougent pas

1. **Aucun chiffre inventé** : un chiffre publié vient de `memoire/faits.md`,
   avec sa source et sa date.
2. **Chaque modification publiée est journalisée** et mesurée à J+28 contre
   un groupe témoin.
3. **Les niveaux d'autonomie** : automatique (title, meta, FAQ, schema,
   maillage), validation (pages neuves, réécritures), interdit (robots.txt,
   redirections, suppression, outreach).
4. **Aucune clé dans un dépôt.** Variables d'environnement seulement.
5. **Une SOP qui change, change pour tous** : elle se modifie ici, jamais
   dans une copie.

## Aller plus loin

| | |
|---|---|
| [docs/sop/](sop/README.md) | les procédures, une par action |
| [docs/PROJETS.md](PROJETS.md) | anatomie d'un projet, synchro, routines, Obsidian |
| [docs/SKILLS.md](SKILLS.md) · [docs/AGENTS.md](AGENTS.md) | ce que fait chaque skill, chaque agent |
| [docs/MCP.md](MCP.md) | brancher Search Console, GA4, le CMS, Notion… |
| [docs/WORKFLOWS.md](WORKFLOWS.md) | les enchaînements types |
| [docs/DEPANNAGE.md](DEPANNAGE.md) · [docs/SECURITE.md](SECURITE.md) | quand ça coince, et ce qu'on ne fait jamais |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | proposer une amélioration |
