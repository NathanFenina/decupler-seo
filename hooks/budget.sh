#!/usr/bin/env bash
# Hook PreToolUse / PostToolUse — plafond de dépenses des API payantes.
#
#   budget.sh avant   (PreToolUse)  : estime l'appel, demande confirmation au-delà
#                                     de seuils.budget_demander_usd, bloque au-delà
#                                     du plafond du mois (seuils.budget_mensuel_usd)
#   budget.sh apres   (PostToolUse) : consigne le coût réel dans .seo-decupler/depenses.csv
#
# Ne bloque jamais par erreur : sans le script, ou s'il échoue, l'appel passe.
set -uo pipefail

RACINE="${SEO_DECUPLER_RACINE:-${HOME}/.claude/seo-decupler}"
SCRIPT="${RACINE}/scripts/budget.py"
[ -f "${SCRIPT}" ] || exit 0
python3 "${SCRIPT}" hook "${1:-avant}" || exit 0
