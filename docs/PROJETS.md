# Piloter des projets en autonomie

decupler-seo s'utilise de deux façons, qui se complètent.

| | Plugin | Projet |
|---|---|---|
| **Pour** | travailler avec Claude, en direct | laisser tourner des routines, sans vous |
| **Installation** | `/plugin install decupler-seo@decupler` | un dépôt privé par site, créé par `projet.py init` ou greffé par `projet.py adopter` |
| **Où vit la méthode** | dans le plugin | copiée dans `.claude/` du dépôt projet |
| **Mémoire** | aucune | `CLAUDE.md` + `memoire/` |
| **Fonctionne dans une routine** | **non** | **oui** |

Pourquoi deux modes : une routine Claude Code tourne dans une session cloud
qui ne charge pas les plugins installés via marketplace. Elle ne voit que ce
qui est commité dans le dépôt qu'elle clone : `CLAUDE.md`, `.claude/skills`,
`.claude/agents`, `.claude/commands`, `.mcp.json`. La méthode doit donc être
**dans** le dépôt du projet.

---

## Anatomie d'un projet

```
mon-projet/                      dépôt PRIVÉ, ouvrable tel quel comme coffre Obsidian
├── Accueil.md                   point d'entrée : liens vers tout ce qui suit
├── CLAUDE.md                    mémoire, chargée à chaque session
├── decupler-seo.config.yml      mode, plafonds, règles propres au client
├── ROUTINES.md                  la routine du mercredi, prête à créer
├── .mcp.json                    serveurs MCP du projet (clés en variables, jamais en clair)
├── .env.example                 les variables attendues, sans valeur
├── memoire/                     CE QU'ON SAIT — écrit par les humains et la routine
│   ├── marque.md  style.md      voix, cible, interdits ; style mesuré sur les pages du client
│   ├── faits.md                 la seule source des chiffres publiés
│   ├── decisions.md             ce qui a été validé ou refusé (lu avant toute proposition)
│   ├── apprentissages.md        ce qui marche sur CE site, mesuré à J+28
│   ├── cartographie.csv         une page = un mot-clé principal + un prompt principal
│   └── entites.csv  triplets.csv  lexique.csv
├── notes/                       BOÎTE D'ENTRÉE HUMAINE — #a-traiter, #fait-client
├── journal/modifications.csv    CE QU'ON A FAIT — chaque modification + son effet à J+28
├── donnees/                     instantanés Search Console, registre d'indexation
├── recherche/                   SERP relevées, benchmarks « faire mieux »
├── rapports/                    mensuels, a-valider.md, runs/ (journal de chaque routine)
├── contenus/                    brouillons
├── routines/                    consignes des routines (hebdo.md…), lues à chaque passage
├── .github/workflows/           sync-methode.yml : PR de mise à jour de la méthode le lundi
├── .obsidian/                   réglages partagés du coffre (l'état de l'écran est ignoré)
└── .claude/
    ├── skills/projet-*          propre au client — jamais touché par la synchro
    ├── agents/projet-*.md       idem pour un agent propre au client
    ├── skills/  agents/  commands/   méthode decupler-seo — synchronisée
    └── decupler-seo/            scripts, modèles, hooks, SOP (docs/sop/), version
```

### Qui écrit quoi

| Couche | Écrit par | Modifiée comment | Jamais |
|---|---|---|---|
| Méthode (`.claude/skills/seo-*`, agents, commandes, scripts, SOP) | decupler-seo | `projet.py sync` (PR du lundi) | modifiée à la main dans un projet : on la remonte (`projet.py remonter`) |
| Spécifique client (`.claude/skills/projet-*`) | vous, Claude | directement dans le projet | dupliquer une méthode générique : on paramètre, on ne recopie pas |
| Mémoire (`memoire/`) | humains, routine | commit | un chiffre absent de `faits.md` |
| Notes (`notes/`) | humains | Obsidian ou éditeur | lues par la routine sans étiquette |
| Journal, données, rapports | scripts, routine | automatique | écrits à la main |
| MCP (`.mcp.json`) et secrets | vous | `.mcp.json` + variables d'environnement | une clé dans le dépôt |

### Skill de méthode ou skill `projet-` ?

Une seule méthode, des paramètres par client. Un savoir-faire qui servirait
sur un autre site va dans decupler-seo, écrit de façon générique, et lit ce
qui change d'un client à l'autre dans le projet : `memoire/marque.md`,
`memoire/style.md`, `decupler-seo.config.yml`, la charte. Un skill
`projet-…` ne garde que ce qui n'a de sens que pour ce client (sa charte
graphique, ses gabarits, ses extensions maison). Jamais deux versions du
même skill : elles divergent dès la deuxième semaine.

### Obsidian

Le dépôt s'ouvre tel quel comme coffre (Obsidian → « Ouvrir un dossier comme
coffre »). Liens Markdown relatifs, pour que GitHub, Obsidian et Claude
lisent les mêmes fichiers ; graphe et rétroliens montrent la mémoire, la
cartographie et les décisions d'un coup d'œil. L'extension communautaire
**Obsidian Git** synchronise avec GitHub (tirer à l'ouverture, pousser
toutes les 10 minutes). Vos idées et retours client vont dans `notes/` avec
`#a-traiter` : la routine du mercredi les transforme en actions. Plusieurs
projets : clonez-les dans un même dossier et ouvrez ce dossier, vous avez un
seul coffre et un graphe commun. Un serveur MCP Obsidian n'apporte rien
ici : Claude lit déjà les fichiers, et il ne tournerait pas dans une routine.

**La règle de partage** : ce qui vaut pour tous les clients est dans
decupler-seo. Ce qui ne vaut que pour un client est dans son projet, dans
`memoire/` ou dans un skill `projet-…`.

---

## Créer un projet

Dans Claude Code, avec le plugin installé : « nouveau projet ». Le skill
`seo-nouveau-projet` pose les questions en une fois, puis lance :

```bash
python3 scripts/projet.py init ../mon-projet \
  --nom "Mon Projet" --domaine https://exemple.com \
  --pays FR --langues fr --cms wordpress --mode assisted
```

Ensuite :
1. compléter `memoire/marque.md`
2. créer le dépôt **privé** sur GitHub et pousser
3. créer les routines de `ROUTINES.md`

## Greffer la méthode sur un dépôt existant

Pour un site dont le code est déjà sur GitHub (Next.js, Astro, Hugo…),
inutile de créer un second dépôt : le projet SEO vit dans celui du site.

```bash
python3 scripts/projet.py adopter ../mon-site \
  --nom "Mon Site" --domaine https://www.exemple.com \
  --pays FR --langues fr,en --cms nextjs --publication depot
```

`adopter` ne détruit rien. Il ajoute seulement les fichiers du gabarit qui
manquent, écrit ses consignes dans `CLAUDE.decupler-seo.md` si un
`CLAUDE.md` existe déjà (à importer depuis celui-ci avec
`@CLAUDE.decupler-seo.md`), complète le `.gitignore` au lieu de le
remplacer, n'ajoute pas de `.mcp.json` (le dépôt a déjà ses connecteurs), et refuse de s'installer si un fichier du dépôt porte le même
nom qu'un fichier de méthode avec un contenu différent — il les liste, vous
décidez. Faites-le sur une branche.

Ensuite, consignez dans `memoire/decisions.md` ce que le projet faisait déjà
et qui prime sur la méthode : une routine de contenu en place (le mode
contenu de `seo-cycle` s'efface alors), un dossier de benchmarks ou une
table des faits existants. La méthode lit ce fichier avant d'agir.

## Deux modes de publication

Dans `decupler-seo.config.yml`, `publication.mode` :

| Mode | Pour | Ce que fait le cycle |
|---|---|---|
| `cms` | WordPress, Webflow | publie par l'API (`scripts/wp.py` pour WordPress), en brouillon ou en ligne selon `publication.statut_par_defaut`, après sauvegarde ; une page déjà en ligne reçoit une révision à valider |
| `depot` | site en code | crée une branche, modifie les fichiers de contenu, lance `controle.commandes` (contrôle des contenus, typage, build), ouvre une pull request. La fusion déclenche le déploiement : elle n'est faite seule qu'en mode `autonomous`, si tous les contrôles sont verts et qu'aucun chiffre n'est douteux ; sinon la PR reste ouverte avec ce qui bloque |

Dans les deux cas, `scripts/controle_contenu.py` passe avant toute
publication et la bloque sur une erreur : texte provisoire, promesse
invérifiable, interdit du client (`regles.interdits`), title ou meta hors
longueur, plusieurs H1. Après publication, `scripts/seo_live.py` vérifie le
site en production : robots.txt, sitemap, chaque URL en 200 sans
redirection, sans noindex, canonical sur elle-même.

## Mettre à jour la méthode dans un projet

```bash
python3 .claude/decupler-seo/scripts/projet.py sync .
```

Récupère la dernière version publiée de decupler-seo et remplace la copie
embarquée. Si un fichier de méthode a été modifié à la main dans le projet,
la synchronisation **refuse** et dit quoi faire : une amélioration de méthode
remonte dans decupler-seo, une règle propre au client va dans un skill
`projet-…`. C'est ce qui empêche dix copies de diverger.

```bash
python3 .claude/decupler-seo/scripts/projet.py statut .
```

### Automatiquement, chaque semaine

Chaque projet créé par `init` ou greffé par `adopter` reçoit
`.github/workflows/sync-methode.yml`. Le lundi, il lance la synchronisation
depuis GitHub et, si la méthode a changé, ouvre une pull request
« Méthode decupler-seo <version> ». Rien n'arrive sur la branche principale
sans votre validation. Une fois par dépôt : Settings › Actions › General ›
« Allow GitHub Actions to create and approve pull requests ».

Pour un projet plus ancien : `projet.py completer .` l'ajoute, avec les
autres nouveautés du gabarit (Accueil.md, notes/, .obsidian/), sans rien
remplacer.

### En travaillant sur un projet : `/seo-maj`

La commande fait le tour dans le bon ordre : statut, remontée des
améliorations faites ici, synchro sur une branche, nouveautés du gabarit,
PR, et la mise à jour du plugin sur votre poste.

### Le chemin retour : une amélioration trouvée chez un client

```bash
python3 .claude/decupler-seo/scripts/projet.py remonter . --pousser
```

Copie les fichiers de méthode modifiés dans ce projet vers decupler-seo, sur
une branche `remontee/<projet>-<date>` (le chemin des scripts est rétabli
dans le Markdown), et la pousse : il reste à ouvrir la pull request. Une
fois fusionnée et publiée, tous les projets la reçoivent le lundi suivant.

### Tous les projets d'un coup d'œil

`projets.json`, à la racine de decupler-seo, liste les dépôts qui embarquent
la méthode. Depuis decupler-seo :

```bash
python3 scripts/projet.py registre
```

affiche, pour chacun, la version embarquée, la présence de la synchro
automatique, et ce qui est à synchroniser. Ajoutez une ligne au registre à
chaque nouveau projet.

### Les SOP

Les procédures (`docs/sop/`) sont embarquées avec la méthode, dans
`.claude/decupler-seo/docs/sop/`. Dans un projet : « suis la SOP brief pour
"<mot-clé>" », Claude lit la fiche et lance le skill qu'elle cite.

---

## Les routines

| Routine | Quand | Publie seule | Vous soumet |
|---|---|---|---|
| Veille | chaque jour | rien | les anomalies |
| Optimisation | lundi | title, meta, FAQ, schema, liens internes | réécritures de sections |
| Contenu | mercredi | rien | les brouillons de pages neuves |
| Rapport | le 1er | le rapport | les retours arrière proposés |

Toutes lancent le skill `seo-cycle` dans le mode correspondant, piloté par
l'agent `seo-manager`. Chaque exécution écrit un journal dans
`rapports/runs/` : un statut vert dans la liste des routines veut seulement
dire que la session s'est terminée sans erreur d'infrastructure, pas que le
travail a été fait. Le rapport mensuel vérifie qu'aucune n'a manqué.

**Deux façons de les créer.** Depuis claude.ai/code/routines, en
choisissant le dépôt du projet : chaque exécution part d'une session neuve,
clonée sur ce dépôt. Ou par l'agent (skill `seo-nouveau-projet`) : l'outil
de création ne permet pas de choisir un dépôt, et une session neuve sans
dépôt ne fait rien — constaté, avec un statut « réussi ». L'agent crée donc
une session dédiée au projet, clonée sur son dépôt, et les routines
s'exécutent dans cette session, chaque consigne commençant par repartir de
`main` à jour. Dans les deux cas, la preuve qu'une routine marche est la
branche qu'elle pousse, pas son statut.

Trois réglages font échouer une routine s'ils sont oubliés :
- **Réseau** : l'environnement par défaut refuse les domaines hors liste.
  Ajoutez le domaine du projet, sinon toute lecture du site renvoie 403.
- **Connecteurs** : une routine utilise toutes les actions d'un connecteur
  inclus, écritures comprises. N'incluez que ceux dont elle a besoin.
- **Clés** : dans l'environnement cloud, jamais dans le dépôt.


### Pièges constatés en production

- **Session vide = faux succès.** Une routine créée par l'agent sans dépôt
  s'affiche « réussie » et ne fait rien. Session dédiée au projet, ou
  routine créée depuis claude.ai/code/routines sur le dépôt.
- **Prompt figé.** Le prompt d'une routine ne se modifie que depuis la
  conversation qui l'a créée. D'où le prompt court qui lit
  `routines/<mode>.md` sur `origin/main` (gabarit dans `ROUTINES.md`).
- **Fusion refusée.** La session peut refuser qu'une routine fusionne sa
  propre PR sans relecture. Les consignes prévoient ce cas : PR laissée
  ouverte, signalée sur la page de suivi, routine terminée. La roadmap est
  publiée avant la livraison git pour ne jamais la perdre.
- **Arbre sale.** Les fichiers de travail du tableau de bord sont dans le
  `.gitignore` du gabarit ; une routine ne supprime jamais un fichier pour
  « nettoyer ».
- **Page de suivi.** Une seule par projet, interne. Lire la version en
  ligne avant de republier (sinon la publication est refusée) ; jamais
  dans un compte rendu lu par le client.

## Travailler projet par projet

Chaque projet se pilote **depuis son propre dépôt**, dans sa propre
conversation : c'est là que vivent sa mémoire (`memoire/`), ses consignes
de routines (`routines/`), sa page de suivi (adresse dans la config) et
ce qu'il reste à faire (`memoire/passation.md` quand il existe).

- **Travail sur le site** : ouvrir le dépôt du projet seul. Le `CLAUDE.md`
  ouvre sur la roadmap ; toute tâche livrée est consignée sur la page de
  suivi (`pilotage.py ajouter`), ce qui évite les doublons entre conversations.
- **Améliorer la méthode** (un skill, un script, un MCP) : ouvrir
  decupler-seo, corriger, tester, publier ; puis dans chaque projet
  `python3 .claude/decupler-seo/scripts/projet.py sync .`. Une règle
  propre à un seul client va dans un skill `projet-…` du dépôt du projet,
  jamais dans la méthode.
- **MCP** : la liste commune est dans `.mcp.json` du gabarit (voir
  `docs/MCP.md`) ; les clés restent dans l'environnement cloud du projet.

---

## La boucle de mesure

Chaque modification publiée est inscrite dans `journal/modifications.csv`
avec ses chiffres Search Console des 28 jours précédents, puis remesurée à
J+28 et comparée à un **groupe témoin** : les pages du site qui n'ont pas
été modifiées. Si tout le site a pris +12 % sur la période, une page à
+17 % n'a gagné que 5 points grâce à la modification.

Tout est automatique quand Search Console est branchée par compte de
service (`GSC_SA_JSON` dans l'environnement de la routine) :

```bash
python3 .claude/decupler-seo/scripts/journal.py ajouter --auto --url … --type title --avant … --apres …
python3 .claude/decupler-seo/scripts/journal.py mesurer-tout --auto
python3 .claude/decupler-seo/scripts/journal.py bilan
```

Le témoin exclut les pages modifiées depuis le début de la période de
référence, et n'est utilisé que s'il pèse au moins 200 clics : sur un petit
site, passer de 20 à 50 clics ferait +150 % et fausserait tout. En dessous
de 20 clics sur la page, le jugement se fait sur la position.

Verdicts : gain, neutre, perte, insuffisant. Les pertes sont proposées au
retour arrière. Au bout de trois mesures du même type, le bilan en tire un
apprentissage dans `memoire/apprentissages.md` — et le cycle en tient compte :
un type de modification qui nuit sur ce site cesse d'être appliqué
automatiquement.

## Les priorités de chaque client

Le moteur de classement est le même pour tous ; ce qui change d'un client à
l'autre, c'est son lexique, `memoire/lexique.csv` : les thèmes de son
métier, la valeur de chacun pour son chiffre d'affaires (1 à 3) et les
motifs qui les reconnaissent, dans toutes ses langues. Le cycle
d'optimisation prend les actions dans l'ordre de `opportunites.py`, et le
rapport mensuel montre les thèmes de valeur encore non couverts.

## Les niveaux d'autonomie

| Niveau | Quoi |
|---|---|
| Automatique | title, meta, FAQ, schema, liens internes sur pages existantes |
| Validation | pages neuves, réécriture de sections sur des pages qui rankent |
| Jamais seul | robots.txt, redirections, canonicals en prod, suppression, outreach, forums, fiche Google |

Plafond par défaut : 3 pages neuves par semaine et par site. Google a mené
trois mises à jour spam en 2026 contre le contenu produit en masse ; la
qualité et la régularité protègent, le volume expose.

Un nouveau projet démarre en mode `assisted` : tout est préparé, rien ne
part sans votre accord. Passez-le en `autonomous` dans
`decupler-seo.config.yml` une fois les premières mesures bonnes.
