# Hooks

Deux hooks optionnels. Ils ne sont pas installés automatiquement : un hook
qui bloque des commandes sans qu'on l'ait demandé est plus pénible qu'utile.

## `garde-fou.sh` — bloquer les écritures non autorisées

Intercepte les commandes qui écrivent sur un site et les passe par
`scripts/guard.py`. Utile si vous laissez Claude tourner sans surveillance.

Dans `~/.claude/settings.json` :

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/seo-decupler/hooks/garde-fou.sh"
          }
        ]
      }
    ]
  }
}
```

Code de sortie 2 = commande bloquée, avec l'explication renvoyée à Claude.

## `verifier-schema.sh` — valider le JSON-LD avant commit

Valide tous les fichiers `.jsonld` du dépôt à chaque commit. Pour les
projets où les schemas sont versionnés.

```bash
ln -s ~/.claude/seo-decupler/hooks/verifier-schema.sh .git/hooks/pre-commit
```
