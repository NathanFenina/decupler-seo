# decupler-seo — règles pour qui maintient la méthode

Ce dépôt est **public** et alimente tous les projets clients.

- **Une modification n'existe que fusionnée dans `main`.** Les projets se
  synchronisent depuis `main` : une branche `claude/…` laissée ouverte est
  perdue pour eux (c'est arrivé : un suivi mensuel complet est resté trois
  semaines sur une branche). Fin de séance = version suivante dans
  `.claude-plugin/plugin.json` et `marketplace.json`, une entrée dans
  `CHANGELOG.md`, tests verts, fusion dans `main`.
- **Tests** : `python3 -m py_compile scripts/*.py && (cd tests && python3 -m unittest discover -q)`.
  Ils vérifient aussi la forme des skills et des agents (`test_structure_skills.py` :
  description ≤ 450 caractères qui dit quoi et quand, budget global, SKILL.md
  ≤ 500 lignes, références reliées) et l'absence de faits périmés
  (`test_faits_canoniques.py`).
- **Évaluations** : `claude plugin eval .` (voir `evals/README.md`). Toute
  règle importante ou tout nouveau skill ajoute un cas ; un skill dont le Δ
  reste nul face à Claude seul est à renforcer ou à fusionner.
- **Skills** : le cas d'usage en tête de la description, une frontière
  « Pas pour … → autre skill » quand deux skills se ressemblent, le détail
  dans `references/` lu au besoin, les règles critiques en haut du fichier.
  Un skill livre toujours le maximum possible avec ce qu'il a (mode dégradé
  signalé) plutôt que de s'arrêter sur une question.
- **Aucun nom de client, aucun chiffre client, aucun accès** ici. Ce qui ne vaut
  que pour un client va dans un skill `projet-…` de son dépôt. Seule exception :
  le registre `projets.json`.
- **Remontées** : les branches `remontee/…` poussées par `projet.py remonter`
  sont fusionnées par le workflow « Intégration des remontées » si les tests
  passent ; sinon il ouvre une issue. Traiter ces issues en priorité.
- **Descente** : chaque lundi, le workflow `sync-methode.yml` de chaque projet
  ouvre une PR « Méthode decupler-seo <version> » (ou, à défaut, une issue).
