# decupler-seo — règles pour qui maintient la méthode

Ce dépôt est **public** et alimente tous les projets clients.

- **Une modification n'existe que fusionnée dans `main`.** Les projets se
  synchronisent depuis `main` : une branche `claude/…` laissée ouverte est
  perdue pour eux (c'est arrivé : un suivi mensuel complet est resté trois
  semaines sur une branche). Fin de séance = version suivante dans
  `.claude-plugin/plugin.json` et `marketplace.json`, une entrée dans
  `CHANGELOG.md`, tests verts, fusion dans `main`.
- **Tests** : `python3 -m py_compile scripts/*.py && (cd tests && python3 -m unittest discover -q)`.
- **Aucun nom de client, aucun chiffre client, aucun accès** ici. Ce qui ne vaut
  que pour un client va dans un skill `projet-…` de son dépôt. Seule exception :
  le registre `projets.json`.
- **Remontées** : les branches `remontee/…` poussées par `projet.py remonter`
  sont fusionnées par le workflow « Intégration des remontées » si les tests
  passent ; sinon il ouvre une issue. Traiter ces issues en priorité.
- **Descente** : chaque lundi, le workflow `sync-methode.yml` de chaque projet
  ouvre une PR « Méthode decupler-seo <version> » (ou, à défaut, une issue).
