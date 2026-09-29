#!/usr/bin/env bash
# Hook pre-commit — valide les fichiers JSON-LD avant de les committer.
set -uo pipefail

RACINE="${SEO_DECUPLER_RACINE:-${HOME}/.claude/seo-decupler}"
VALIDEUR="${RACINE}/scripts/schema_validate.py"
[ -f "${VALIDEUR}" ] || VALIDEUR="scripts/schema_validate.py"
[ -f "${VALIDEUR}" ] || exit 0

FICHIERS="$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.jsonld$' || true)"
[ -n "${FICHIERS}" ] || exit 0

ECHECS=0
while IFS= read -r fichier; do
    [ -f "${fichier}" ] || continue
    if ! python3 -c "import json,sys; json.load(open(sys.argv[1]))" "${fichier}" 2>/dev/null; then
        printf '  ✗ %s : JSON invalide — le bloc entier serait ignoré par Google.\n' "${fichier}" >&2
        ECHECS=$((ECHECS + 1))
        continue
    fi
    python3 "${VALIDEUR}" "${fichier}" 2>/dev/null | grep -q '🔴' && {
        printf '  ! %s : propriétés requises manquantes.\n' "${fichier}" >&2
        python3 "${VALIDEUR}" "${fichier}" 2>/dev/null | grep -A1 '🔴' >&2
    }
done <<< "${FICHIERS}"

if [ "${ECHECS}" -gt 0 ]; then
    printf '\n  %s fichier(s) JSON-LD invalide(s). Commit interrompu.\n\n' "${ECHECS}" >&2
    exit 1
fi
exit 0
