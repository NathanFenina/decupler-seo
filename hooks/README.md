# Hooks

Trois hooks optionnels. Ils ne sont pas installés automatiquement : un hook
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

## `budget.sh` — plafonner les dépenses d'API

Avant chaque appel à un MCP payant (DataForSEO, Ahrefs, Semrush, Firecrawl,
Perplexity, Ubersuggest), estime son coût ; demande une confirmation au-delà
de `seuils.budget_demander_usd` (0,50 $ par défaut) et bloque l'appel si le
plafond du mois `seuils.budget_mensuel_usd` est atteint. Après l'appel,
consigne le coût réel (DataForSEO le renvoie) dans `.seo-decupler/depenses.csv`.
`python3 scripts/budget.py etat` donne la dépense du mois par outil.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__.*(dataforseo|ahrefs|semrush|firecrawl|perplexity|ubersuggest).*",
        "hooks": [{ "type": "command", "command": "~/.claude/seo-decupler/hooks/budget.sh avant" }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "mcp__.*(dataforseo|ahrefs|semrush|firecrawl|perplexity|ubersuggest).*",
        "hooks": [{ "type": "command", "command": "~/.claude/seo-decupler/hooks/budget.sh apres" }]
      }
    ]
  }
}
```

`demande.py` consigne lui-même ses appels DataForSEO dans le même journal.

## `verifier-schema.sh` — valider le JSON-LD avant commit

Valide tous les fichiers `.jsonld` du dépôt à chaque commit. Pour les
projets où les schemas sont versionnés.

```bash
ln -s ~/.claude/seo-decupler/hooks/verifier-schema.sh .git/hooks/pre-commit
```
