#!/usr/bin/env bash
set -euo pipefail

# Désinstallation de Claude Code SEO Décupler.
# Ne touche jamais à vos sorties (seo-output/) ni à votre .env.

CLAUDE="${HOME}/.claude"
RACINE="${CLAUDE}/seo-decupler"

printf '\n  Désinstallation de Claude Code SEO Décupler\n\n'

# On ne supprime que les skills du dispositif, jamais les vôtres.
SUPPRIMES=0
for dossier in "${CLAUDE}"/skills/seo-* "${CLAUDE}"/skills/geo-*; do
    [ -d "${dossier}" ] || continue
    rm -rf "${dossier}"
    SUPPRIMES=$((SUPPRIMES + 1))
done
printf '  → %s skills supprimés\n' "${SUPPRIMES}"

for agent in seo-technique seo-performance seo-contenu seo-redacteur seo-data \
             seo-serp seo-schema seo-geo seo-netlinking seo-frontend \
             seo-crawler seo-strategiste seo-publisher seo-analyste-concurrence seo-manager; do
    rm -f "${CLAUDE}/agents/${agent}.md"
done
printf '  → agents supprimés\n'

rm -f "${CLAUDE}"/commands/seo.md "${CLAUDE}"/commands/seo-*.md
printf '  → commandes supprimées\n'

if [ -f "${RACINE}/.env" ]; then
    printf '\n  ⚠️  %s/.env contient vos clés API.\n' "${RACINE}"
    printf '     Il est conservé. Supprimez-le vous-même si vous le souhaitez :\n'
    printf '     rm -rf %s\n' "${RACINE}"
else
    rm -rf "${RACINE}"
    printf '  → scripts et configuration supprimés\n'
fi

printf '\n  ✓ Désinstallé.\n\n'
