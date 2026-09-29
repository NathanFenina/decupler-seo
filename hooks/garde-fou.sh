#!/usr/bin/env bash
# Hook PreToolUse — passe les commandes d'écriture par le garde-fou.
#
# Lit l'appel d'outil sur stdin (JSON), en extrait la commande, et bloque
# (code 2) si le garde-fou refuse. Voir hooks/README.md pour l'installer.

set -uo pipefail

RACINE="${SEO_DECUPLER_RACINE:-${HOME}/.claude/seo-decupler}"
GARDE="${RACINE}/scripts/guard.py"
[ -f "${GARDE}" ] || exit 0   # pas installé : on ne bloque rien

ENTREE="$(cat)"
COMMANDE="$(printf '%s' "${ENTREE}" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | cut -d'"' -f4)"
[ -n "${COMMANDE}" ] || exit 0

# On ne s'intéresse qu'aux commandes qui écrivent quelque part hors de la
# machine locale. Le reste passe sans contrôle.
detecter_action() {
    case "${COMMANDE}" in
        *wp-json*POST*|*wp-json*PUT*|*wp-json*PATCH*) echo "publier" ;;
        *api.webflow.com*POST*|*api.webflow.com*PATCH*) echo "publier" ;;
        *robots.txt*\>*|*"robots.txt"*tee*) echo "modifier-robots" ;;
        *.htaccess*\>*|*"redirect"*\>*) echo "modifier-redirections" ;;
        *oauth.reddit.com*submit*|*reddit.com/api/submit*) echo "poster-communaute" ;;
        *sendmail*|*"smtp"*send*|*mailgun*|*sendgrid*) echo "envoyer-email" ;;
        *) echo "" ;;
    esac
}

ACTION="$(detecter_action)"
[ -n "${ACTION}" ] || exit 0

CIBLE="$(printf '%s' "${COMMANDE}" | grep -oE 'https?://[^ "'"'"']+' | head -1)"

SORTIE="$(python3 "${GARDE}" --action "${ACTION}" ${CIBLE:+--cible "${CIBLE}"} 2>/dev/null)"
CODE=$?

case "${CODE}" in
    0) exit 0 ;;
    1)
        printf 'Garde-fou : validation humaine requise avant « %s ».\n%s\n' \
               "${ACTION}" "${SORTIE}" >&2
        exit 2 ;;
    *)
        printf 'Garde-fou : action « %s » bloquée.\n%s\n' "${ACTION}" "${SORTIE}" >&2
        exit 2 ;;
esac
