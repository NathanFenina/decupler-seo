#!/usr/bin/env bash
set -euo pipefail

# ══════════════════════════════════════════════════════════════════
#  Claude Code SEO Décupler — installation
#  https://github.com/NathanFenina/decupler-seo
# ══════════════════════════════════════════════════════════════════
#
# Tout est enveloppé dans main() pour qu'une coupure réseau pendant un
# `curl | bash` n'exécute jamais une moitié de script.

main() {
    local DEPOT="https://github.com/NathanFenina/decupler-seo"
    local CLAUDE="${HOME}/.claude"
    local RACINE="${CLAUDE}/seo-decupler"

    printf '\n'
    printf '  ╔════════════════════════════════════════════════╗\n'
    printf '  ║   Claude Code SEO Décupler                     ║\n'
    printf '  ║   36 skills · 15 agents · 13 MCP               ║\n'
    printf '  ╚════════════════════════════════════════════════╝\n\n'

    # ─── Prérequis ────────────────────────────────────────────────
    command -v git >/dev/null 2>&1 || {
        printf '  ✗ Git est requis. Installez-le puis relancez.\n\n'; exit 1; }

    local PY=""
    for candidat in python3 python; do
        if command -v "${candidat}" >/dev/null 2>&1; then PY="${candidat}"; break; fi
    done
    [ -n "${PY}" ] || { printf '  ✗ Python 3.8+ est requis.\n\n'; exit 1; }

    printf '  ✓ Python %s\n' "$(${PY} -c 'import sys;print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    command -v node >/dev/null 2>&1 \
        && printf '  ✓ Node %s\n' "$(node -v)" \
        || printf '  ! Node absent — les MCP en npx ne démarreront pas.\n'

    # ─── Récupération ─────────────────────────────────────────────
    local TEMPO
    TEMPO="$(mktemp -d)"
    trap 'rm -rf "${TEMPO}"' EXIT

    printf '\n  ↓ Téléchargement…\n'
    if [ -f "$(dirname "$0")/.claude-plugin/plugin.json" ]; then
        # Lancé depuis un clone local : on installe depuis les fichiers présents.
        cp -R "$(dirname "$0")" "${TEMPO}/source"
    else
        git clone --depth 1 --quiet "${DEPOT}" "${TEMPO}/source"
    fi
    local SRC="${TEMPO}/source"

    # ─── Installation ─────────────────────────────────────────────
    printf '  → Skills…\n'
    mkdir -p "${CLAUDE}/skills"
    for dossier in "${SRC}"/skills/*/; do
        [ -d "${dossier}" ] || continue
        local nom; nom="$(basename "${dossier}")"
        mkdir -p "${CLAUDE}/skills/${nom}"
        cp -R "${dossier}." "${CLAUDE}/skills/${nom}/"
    done
    printf '    %s skills\n' "$(find "${SRC}/skills" -maxdepth 1 -mindepth 1 -type d | wc -l | tr -d ' ')"

    printf '  → Agents…\n'
    mkdir -p "${CLAUDE}/agents"
    cp "${SRC}"/agents/*.md "${CLAUDE}/agents/" 2>/dev/null || true

    printf '  → Commandes…\n'
    mkdir -p "${CLAUDE}/commands"
    cp "${SRC}"/commands/*.md "${CLAUDE}/commands/" 2>/dev/null || true

    printf '  → Scripts, config et modèles…\n'
    mkdir -p "${RACINE}"
    for element in scripts config schema templates hooks docs; do
        [ -d "${SRC}/${element}" ] && cp -R "${SRC}/${element}" "${RACINE}/"
    done
    cp "${SRC}/requirements.txt" "${RACINE}/" 2>/dev/null || true
    cp "${SRC}/.mcp.json" "${RACINE}/" 2>/dev/null || true
    chmod +x "${RACINE}"/scripts/*.py 2>/dev/null || true
    chmod +x "${RACINE}"/hooks/*.sh 2>/dev/null || true

    # Installé en plugin, Claude Code remplace ${CLAUDE_PLUGIN_ROOT} par le
    # dossier du plugin. Copiés à la main dans ~/.claude, les skills ne sont
    # pas substitués : on écrit donc le chemin d'installation en dur.
    printf '  → Chemins des scripts…\n'
    "${PY}" - "${RACINE}" "${CLAUDE}" "${SRC}" <<'PYEOF'
import sys
from pathlib import Path

racine, claude, src = (Path(a) for a in sys.argv[1:4])
cibles = []
for dossier in (src / "skills").iterdir():
    if dossier.is_dir():
        cibles += (claude / "skills" / dossier.name).rglob("*.md")
cibles += (claude / "agents" / f.name for f in (src / "agents").glob("*.md"))
cibles += (claude / "commands" / f.name for f in (src / "commands").glob("*.md"))

jeton, ajustes = "${CLAUDE_PLUGIN_ROOT}", 0
for fichier in cibles:
    if fichier.is_file():
        texte = fichier.read_text(encoding="utf-8")
        if jeton in texte:
            fichier.write_text(texte.replace(jeton, str(racine)), encoding="utf-8")
            ajustes += 1
print(f"    {ajustes} fichiers pointés vers {racine}")
PYEOF

    # ─── Dépendances Python ───────────────────────────────────────
    printf '  → Dépendances Python…\n'
    local VENV="${RACINE}/.venv"
    if ${PY} -m venv "${VENV}" 2>/dev/null && [ -x "${VENV}/bin/pip" ]; then
        if "${VENV}/bin/pip" install --quiet --upgrade pip >/dev/null 2>&1 \
           && "${VENV}/bin/pip" install --quiet -r "${RACINE}/requirements.txt" >/dev/null 2>&1; then
            printf '    ✓ installées dans %s\n' "${VENV}"
        else
            printf '    ! échec. Relancez : %s/bin/pip install -r %s/requirements.txt\n' \
                   "${VENV}" "${RACINE}"
        fi
    else
        ${PY} -m pip install --quiet --user -r "${RACINE}/requirements.txt" 2>/dev/null \
            && printf '    ✓ installées (--user)\n' \
            || printf '    ! échec. Relancez : pip install --user -r %s/requirements.txt\n' "${RACINE}"
    fi

    # ─── Fichier de config utilisateur ────────────────────────────
    if [ ! -f "${RACINE}/.env" ] && [ -f "${RACINE}/config/.env.example" ]; then
        cp "${RACINE}/config/.env.example" "${RACINE}/.env"
        printf '  → Modèle de configuration créé : %s/.env\n' "${RACINE}"
    fi

    # ─── Fin ──────────────────────────────────────────────────────
    printf '\n'
    printf '  ✓ Installé.\n\n'
    printf '  Prochaine étape — dans Claude Code :\n\n'
    printf '      /seo doctor\n\n'
    printf '  Il vous dira quoi brancher, dans quel ordre, et lancera\n'
    printf '  la première action utile.\n\n'
    printf '  Configuration : %s/.env\n' "${RACINE}"
    printf '  Documentation : %s/docs/\n\n' "${RACINE}"
}

main "$@"
