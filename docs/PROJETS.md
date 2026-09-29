# Piloter des projets en autonomie

decupler-seo s'utilise de deux façons, qui se complètent.

| | Plugin | Projet |
|---|---|---|
| **Pour** | travailler avec Claude, en direct | laisser tourner des routines, sans vous |
| **Installation** | `/plugin install decupler-seo@decupler` | un dépôt privé par site, créé par `projet.py init` |
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
mon-projet/                      dépôt PRIVÉ
├── CLAUDE.md                    mémoire, chargée à chaque session
├── decupler-seo.config.yml      mode, plafonds, règles propres au client
├── ROUTINES.md                  les 4 routines, prêtes à créer
├── .mcp.json                    serveurs MCP lus par les routines
├── memoire/
│   ├── marque.md                voix, lexique, chiffres officiels, interdits
│   ├── decisions.md             ce qui a été validé ou refusé
│   └── apprentissages.md        ce qui marche sur CE site, mesuré
├── journal/
│   └── modifications.csv        chaque modification + son effet à J+28
├── donnees/                     instantanés Search Console
├── rapports/                    mensuels, à valider, journaux de run
├── contenus/                    brouillons
└── .claude/
    ├── skills/projet-*          propre au client — jamais touché par la synchro
    ├── skills/…                 méthode decupler-seo — synchronisée
    ├── agents/  commands/       méthode decupler-seo — synchronisée
    └── decupler-seo/            scripts, modèles, version
```

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

Trois réglages font échouer une routine s'ils sont oubliés :
- **Réseau** : l'environnement par défaut refuse les domaines hors liste.
  Ajoutez le domaine du projet, sinon toute lecture du site renvoie 403.
- **Connecteurs** : une routine utilise toutes les actions d'un connecteur
  inclus, écritures comprises. N'incluez que ceux dont elle a besoin.
- **Clés** : dans l'environnement cloud, jamais dans le dépôt.

---

## La boucle de mesure

Chaque modification publiée est inscrite dans `journal/modifications.csv`
avec ses chiffres Search Console des 28 jours précédents, puis remesurée à
J+28 et comparée à un **groupe témoin** : les pages du site qui n'ont pas
été modifiées. Si tout le site a pris +12 % sur la période, une page à
+17 % n'a gagné que 5 points grâce à la modification.

Verdicts : gain, neutre, perte, insuffisant. Les pertes sont proposées au
retour arrière. Au bout de trois mesures du même type, le bilan en tire un
apprentissage dans `memoire/apprentissages.md` — et le cycle en tient compte :
un type de modification qui nuit sur ce site cesse d'être appliqué
automatiquement.

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
