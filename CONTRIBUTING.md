# Contribuer

Les contributions sont bienvenues.

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

- Stdlib uniquement quand c'est possible
- `requests` et `beautifulsoup4` sont acceptables (déjà dans les dépendances)
- Français pour les messages utilisateur, les noms de variables et les
  commentaires
- Un commentaire n'explique jamais *ce que fait* le code, mais *pourquoi*

## Avant d'ouvrir une PR

```bash
python3 -m py_compile scripts/*.py
python3 scripts/doctor.py
python3 scripts/guard.py --statut
```

Décrivez ce que votre changement apporte, et ce qu'il ne couvre pas.
