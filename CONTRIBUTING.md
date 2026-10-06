# Contribuer

Les contributions sont bienvenues.

## Remonter une amélioration trouvée sur un projet

C'est le cas le plus fréquent : en travaillant chez un client, vous corrigez
un skill, une SOP ou un script embarqué dans `.claude/`. Depuis le projet :

```bash
python3 .claude/decupler-seo/scripts/projet.py remonter . --pousser
```

Le script copie les fichiers de méthode modifiés vers decupler-seo, sur une
branche `remontee/<projet>-<date>`, en rétablissant les chemins
`${CLAUDE_PLUGIN_ROOT}` du Markdown. Ouvrez la pull request, décrivez le cas
réel qui l'a motivée, et retirez tout ce qui est propre au client (nom,
domaine, chiffres) : ce dépôt est public.

## Ajouter un skill

1. Créez `skills/<nom>/SKILL.md`
2. Frontmatter obligatoire :
   ```yaml
   ---
   name: mon-skill
   description: >
     Ce que fait le skill, puis les formulations qui doivent le déclencher.
     La description est ce qui décide du déclenchement : soyez précis sur les
     mots que l'utilisateur emploiera réellement.
   ---
   ```
3. Le corps : la méthode, pas la théorie. Un skill utile dit **quoi faire**,
   dans quel ordre, avec quels seuils.

### Ce qui fait un bon skill ici

- Des **seuils chiffrés**, pas des « il faut optimiser »
- Le **correctif écrit**, pas la recommandation
- Les **pièges connus** : ce qui échoue habituellement et pourquoi
- L'**honnêteté sur les limites** : ce que le skill ne peut pas faire
- Les livrables nommés

### Ce qu'on refuse

- Les affirmations non vérifiables sur le fonctionnement de Google
- Les techniques qui violent les règles des plateformes
- Tout ce qui automatise une publication communautaire ou un envoi d'email
- Les chiffres sans source

## Ajouter un MCP

Ajoutez l'entrée dans `.mcp.json` avec ses champs `_role` et `_obtenir`,
la variable dans `config/.env.example`, et la ligne correspondante dans
`OUTILS` de `scripts/doctor.py`. Documentez le branchement dans `docs/MCP.md`.

## Ajouter un agent

`agents/<nom>.md`, avec `name`, `description` et `tools` en frontmatter.
Gardez-le court et spécialisé : un agent qui fait tout ne fait rien bien.

## Les scripts Python

- Python 3.10+. **Bibliothèque standard uniquement** pour tout ce qui tourne
  dans une routine cloud (`guard`, `projet`, `journal`, `gsc`,
  `controle_contenu`, `seo_live`, `doctor`) : rien n'y est installé.
- `requests` et `beautifulsoup4` sont acceptables pour les scripts
  d'analyse de pages, déjà dans les dépendances.
- Les réglages d'un projet se lisent avec `lire_valeur("section.cle")` et
  `lire_liste(...)` de `scripts/_projet.py` — jamais en relisant le YAML à
  la main : la configuration est imbriquée, et deux clés `mode` n'ont pas le
  même sens selon leur section.
- Dans un skill ou une commande, un script s'appelle par
  `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/<script>.py"`, jamais par un
  chemin relatif : le dossier courant est celui du projet, pas du plugin.
- Français pour les messages utilisateur, les noms de variables et les
  commentaires.
- Un commentaire n'explique jamais *ce que fait* le code, mais *pourquoi*.
- Aucun secret affiché : un script peut dire qu'une clé est présente ou
  invalide, jamais en imprimer la valeur.

## Tests

```bash
cd tests && python3 -m unittest discover -v
```

Chaque test tourne dans un dossier temporaire, sans réseau, avec un
environnement débarrassé des variables `SEO_`, `GSC_`, `WP_`… de votre
machine. Un correctif de script vient avec le test qui l'aurait attrapé.

## Avant d'ouvrir une PR

```bash
python3 -m py_compile scripts/*.py
(cd tests && python3 -m unittest discover)
claude plugin validate .
```

L'intégration continue rejoue ces trois contrôles sur Python 3.10 et 3.13,
puis crée un projet de bout en bout et vérifie qu'aucun `{{…}}` n'y reste.

Décrivez ce que votre changement apporte, et ce qu'il ne couvre pas.
