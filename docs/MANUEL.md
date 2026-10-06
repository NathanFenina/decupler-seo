# Manuel — prendre en main decupler-seo

Ce dépôt est **une seule source de savoir SEO et GEO** : les procédures
(SOP), les skills qui les exécutent, les scripts qui mesurent, et le
gabarit d'un projet client. On l'utilise de trois façons. Trouvez la vôtre,
suivez ses étapes dans l'ordre, et vous n'avez rien d'autre à lire pour
commencer.

| Vous êtes | Votre chemin | Temps |
|---|---|---|
| Vous découvrez, vous voulez l'essayer sur votre site | [A. Essayer](#a-essayer-le-plugin-sur-votre-site) | 10 minutes |
| Prestataire sur un projet qui l'utilise déjà | [B. Rejoindre un projet](#b-rejoindre-un-projet-existant) | 30 minutes |
| Consultant ou agence, plusieurs sites à piloter | [C. Piloter des projets](#c-piloter-des-projets-en-autonomie) | une demi-journée par projet |

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
4. Créer **une** routine, le vendredi : [modele-projet/ROUTINES.md](../modele-projet/ROUTINES.md).
5. Ajouter le dépôt à `projets.json` ; `projet.py registre` montre l'état de
   tous les projets.
6. Votre semaine : [SOP 15 · La semaine type](sop/15-semaine-type.md). Vos
   choix du mois : [SOP 16 · Arbitrer les actions](sop/16-arbitrer-les-actions.md).

Optionnel : ouvrir le dépôt comme coffre Obsidian pour lire et annoter la
mémoire ([docs/PROJETS.md](PROJETS.md#obsidian)).

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
