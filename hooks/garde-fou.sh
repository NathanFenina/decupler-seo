#!/usr/bin/env bash
# Hook PreToolUse — passe les commandes d'écriture par le garde-fou.
#
# Lit l'appel d'outil sur stdin (JSON), en extrait la commande, et bloque
# (code 2) si le garde-fou refuse. Activé d'office par le plugin
# (hooks/hooks.json) et par le modèle de projet (.claude/settings.json).
#
# Les scripts de la méthode (wp.py, indexation.py…) appellent déjà guard.py
# eux-mêmes : ce hook rattrape les écritures improvisées hors de ces
# scripts (curl vers l'API WordPress, robots.txt réécrit à la main…).

set -uo pipefail

# guard.py est à côté de ce hook : hooks/ et scripts/ sont frères, que la
# méthode soit installée en plugin ou embarquée sous .claude/decupler-seo/.
ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RACINE="${SEO_DECUPLER_RACINE:-$(dirname "${ICI}")}"
GARDE="${RACINE}/scripts/guard.py"
[ -f "${GARDE}" ] || GARDE="${HOME}/.claude/seo-decupler/scripts/guard.py"
[ -f "${GARDE}" ] || exit 0   # méthode absente : on ne bloque rien

COMMANDE="$(python3 -c 'import json,sys
try:
    print(json.load(sys.stdin).get("tool_input", {}).get("command", ""))
except Exception:
    pass' 2>/dev/null)"
[ -n "${COMMANDE}" ] || exit 0

ecrit() { printf '%s' "${COMMANDE}" | grep -qiE -- '-X[[:space:]]*(POST|PUT|PATCH|DELETE)|--request[[:space:]=]*(POST|PUT|PATCH|DELETE)|(^|[[:space:]])(-d|--data[a-z-]*|-F|--form)([[:space:]=]|$)'; }
# Dépôt d'un fichier sur un serveur (FTP, SCP, rsync, upload curl).
envoie() { printf '%s' "${COMMANDE}" | grep -qiE -- '(^|[[:space:]])(l?ftp|sftp|scp|rsync|ncftpput|wput)[[:space:]]|curl[^|]*(-T|--upload-file)[[:space:]]|deploy\.sh'; }
contient() { printf '%s' "${COMMANDE}" | grep -qiE -- "$1"; }

# On ne s'intéresse qu'aux commandes qui écrivent quelque part hors de la
# machine locale. Le reste passe sans contrôle.
ACTION=""
if contient 'wp-json|xmlrpc\.php' && ecrit; then ACTION="publier"
elif contient 'api\.webflow\.com' && ecrit; then ACTION="publier"
elif contient 'robots\.txt' && envoie; then ACTION="modifier-robots"
elif contient '\.htaccess' && envoie; then ACTION="modifier-redirections"
elif contient 'oauth\.reddit\.com.*submit|reddit\.com/api/submit'; then ACTION="poster-communaute"
elif contient 'sendmail|api\.mailgun\.net|api\.sendgrid\.com|api\.brevo\.com/v3/smtp'; then ACTION="envoyer-email"
fi
[ -n "${ACTION}" ] || exit 0

CIBLE="$(printf '%s' "${COMMANDE}" | grep -oE 'https?://[^ "'"'"']+' | head -1)"

# guard.py lit la configuration du projet dans le dossier courant.
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || true
SORTIE="$(python3 "${GARDE}" --action "${ACTION}" ${CIBLE:+--cible "${CIBLE}"} 2>/dev/null)"
CODE=$?

case "${CODE}" in
    0) exit 0 ;;
    1)
        printf 'Garde-fou : validation humaine requise avant « %s ». Demande le feu vert à l'"'"'utilisateur, puis passe par le script de la méthode (wp.py…).\n%s\n' \
               "${ACTION}" "${SORTIE}" >&2
        exit 2 ;;
    *)
        printf 'Garde-fou : action « %s » bloquée.\n%s\n' "${ACTION}" "${SORTIE}" >&2
        exit 2 ;;
esac
