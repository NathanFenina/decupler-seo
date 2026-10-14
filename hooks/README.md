# Hooks

Trois hooks. Le garde-fou est actif d'office ; les deux autres sont optionnels.

## `garde-fou.sh` — bloquer les écritures non autorisées (actif d'office)

Avant chaque commande Bash, repère les écritures qui partent hors de la
machine et les passe par `scripts/guard.py` :

- appel en écriture à l'API WordPress ou Webflow (`POST`, `PUT`, `PATCH`,
  `DELETE`, `-d`, `--data`, `-F`), quel que soit l'ordre des options ;
- envoi de `robots.txt` ou `.htaccess` sur un serveur (FTP, SCP, rsync,
  upload curl, `deploy.sh`) ;
- publication Reddit, envoi d'email (sendmail, Mailgun, SendGrid, Brevo).

Les lectures passent sans contrôle. Les scripts de la méthode (`wp.py`…)
appellent déjà le garde-fou eux-mêmes : le hook rattrape ce qui serait
improvisé à côté. Verdict : autorisé → la commande part ; validation requise
ou bloqué → code 2, et Claude reçoit l'explication.

C'est le seul hook installé d'office :

- plugin : `hooks/hooks.json`, chargé avec le plugin ;
- projet embarqué : `.claude/settings.json` du gabarit (`modele-projet/`).
  Projet existant sans ce fichier : `projet.py completer .` ; s'il a déjà un
  `.claude/settings.json`, ajoutez-y le bloc `hooks` du gabarit.

Pour le couper ponctuellement : retirez le bloc `hooks`, ou passez le projet
en `mode: autonomous` avec ses domaines dans `SEO_ALLOWED_DOMAINS`.

## `budget.sh` — plafonner les dépenses d'API

Avant chaque appel à un MCP payant (DataForSEO, Ahrefs, Semrush, Firecrawl,
Perplexity, Ubersuggest, Treg, Monid), estime son coût ; demande une confirmation au-delà
de `seuils.budget_demander_usd` (0,50 $ par défaut) et bloque l'appel si le
plafond du mois `seuils.budget_mensuel_usd` est atteint. Après l'appel,
consigne le coût réel (DataForSEO le renvoie) dans `.seo-decupler/depenses.csv`.
`python3 scripts/budget.py etat` donne la dépense du mois par outil.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__.*(dataforseo|ahrefs|semrush|firecrawl|perplexity|ubersuggest|treg|monid).*",
        "hooks": [{ "type": "command", "command": "~/.claude/seo-decupler/hooks/budget.sh avant" }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "mcp__.*(dataforseo|ahrefs|semrush|firecrawl|perplexity|ubersuggest|treg|monid).*",
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
