#!/usr/bin/env bash
# Copie le mini-projet fictif dans l'espace de travail du cas (cwd).
set -euo pipefail
ICI="$(cd "$(dirname "$0")" && pwd)"
cp -R "$ICI/." .
rm -f preparer.sh README.md
