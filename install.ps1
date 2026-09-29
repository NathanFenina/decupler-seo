# ══════════════════════════════════════════════════════════════════
#  Claude Code SEO Décupler — installation Windows
#  https://github.com/NathanFenina/decupler-seo
# ══════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"

function Install-SeoDecupler {
    $Depot  = "https://github.com/NathanFenina/decupler-seo"
    $Claude = Join-Path $HOME ".claude"
    $Racine = Join-Path $Claude "seo-decupler"

    Write-Host ""
    Write-Host "  ╔════════════════════════════════════════════════╗"
    Write-Host "  ║   Claude Code SEO Décupler                     ║"
    Write-Host "  ║   36 skills · 15 agents · 13 MCP               ║"
    Write-Host "  ╚════════════════════════════════════════════════╝"
    Write-Host ""

    # ─── Prérequis ────────────────────────────────────────────────
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Host "  ✗ Git est requis. Installez-le puis relancez." -ForegroundColor Red
        return
    }

    $Py = $null
    foreach ($c in @("python", "python3", "py")) {
        if (Get-Command $c -ErrorAction SilentlyContinue) { $Py = $c; break }
    }
    if (-not $Py) {
        Write-Host "  ✗ Python 3.8+ est requis." -ForegroundColor Red
        return
    }
    $Version = & $Py -c "import sys;print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    Write-Host "  ✓ Python $Version"

    if (Get-Command node -ErrorAction SilentlyContinue) {
        Write-Host "  ✓ Node $(node -v)"
    } else {
        Write-Host "  ! Node absent — les MCP en npx ne démarreront pas." -ForegroundColor Yellow
    }

    # ─── Récupération ─────────────────────────────────────────────
    $Tempo = Join-Path ([System.IO.Path]::GetTempPath()) ("seo-dcp-" + [guid]::NewGuid())
    New-Item -ItemType Directory -Path $Tempo -Force | Out-Null

    try {
        Write-Host ""
        Write-Host "  ↓ Téléchargement…"
        $Src = Join-Path $Tempo "source"
        if (Test-Path (Join-Path $PSScriptRoot ".claude-plugin\plugin.json")) {
            Copy-Item -Recurse -Force $PSScriptRoot $Src
        } else {
            git clone --depth 1 --quiet $Depot $Src
        }

        # ─── Installation ─────────────────────────────────────────
        Write-Host "  → Skills…"
        $DossierSkills = Join-Path $Claude "skills"
        New-Item -ItemType Directory -Path $DossierSkills -Force | Out-Null
        $Skills = Get-ChildItem (Join-Path $Src "skills") -Directory
        foreach ($s in $Skills) {
            $Cible = Join-Path $DossierSkills $s.Name
            New-Item -ItemType Directory -Path $Cible -Force | Out-Null
            Copy-Item -Recurse -Force (Join-Path $s.FullName "*") $Cible
        }
        Write-Host "    $($Skills.Count) skills"

        Write-Host "  → Agents…"
        $DossierAgents = Join-Path $Claude "agents"
        New-Item -ItemType Directory -Path $DossierAgents -Force | Out-Null
        Copy-Item -Force (Join-Path $Src "agents\*.md") $DossierAgents -ErrorAction SilentlyContinue

        Write-Host "  → Commandes…"
        $DossierCmd = Join-Path $Claude "commands"
        New-Item -ItemType Directory -Path $DossierCmd -Force | Out-Null
        Copy-Item -Force (Join-Path $Src "commands\*.md") $DossierCmd -ErrorAction SilentlyContinue

        Write-Host "  → Scripts, config et modèles…"
        New-Item -ItemType Directory -Path $Racine -Force | Out-Null
        foreach ($e in @("scripts", "config", "schema", "templates", "hooks", "docs")) {
            $Chemin = Join-Path $Src $e
            if (Test-Path $Chemin) { Copy-Item -Recurse -Force $Chemin $Racine }
        }
        Copy-Item -Force (Join-Path $Src "requirements.txt") $Racine -ErrorAction SilentlyContinue
        Copy-Item -Force (Join-Path $Src ".mcp.json") $Racine -ErrorAction SilentlyContinue

        # Hors plugin, ${CLAUDE_PLUGIN_ROOT} n'est pas substitué par Claude
        # Code : on écrit le chemin d'installation en dur. Barres obliques,
        # pour que le chemin reste valide dans le shell de Claude.
        Write-Host "  → Chemins des scripts…"
        $Jeton = '${CLAUDE_PLUGIN_ROOT}'
        $RacineSlash = $Racine -replace '\\', '/'
        $Cibles = @()
        foreach ($s in $Skills) {
            $Cibles += Get-ChildItem (Join-Path $DossierSkills $s.Name) -Recurse -Filter *.md
        }
        $Cibles += Get-ChildItem (Join-Path $Src "agents") -Filter *.md |
            ForEach-Object { Get-Item (Join-Path $DossierAgents $_.Name) -ErrorAction SilentlyContinue }
        $Cibles += Get-ChildItem (Join-Path $Src "commands") -Filter *.md |
            ForEach-Object { Get-Item (Join-Path $DossierCmd $_.Name) -ErrorAction SilentlyContinue }
        $Ajustes = 0
        foreach ($f in ($Cibles | Where-Object { $_ })) {
            $Texte = [IO.File]::ReadAllText($f.FullName)
            if ($Texte.Contains($Jeton)) {
                [IO.File]::WriteAllText($f.FullName, $Texte.Replace($Jeton, $RacineSlash))
                $Ajustes++
            }
        }
        Write-Host "    $Ajustes fichiers pointés vers $RacineSlash"

        # ─── Dépendances Python ───────────────────────────────────
        Write-Host "  → Dépendances Python…"
        $Venv = Join-Path $Racine ".venv"
        $Reqs = Join-Path $Racine "requirements.txt"
        & $Py -m venv $Venv 2>$null
        $VenvPip = Join-Path $Venv "Scripts\pip.exe"
        if (Test-Path $VenvPip) {
            & $VenvPip install --quiet -r $Reqs 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "    ✓ installées dans $Venv"
            } else {
                Write-Host "    ! échec. Relancez : $VenvPip install -r $Reqs" -ForegroundColor Yellow
            }
        } else {
            & $Py -m pip install --quiet --user -r $Reqs 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "    ✓ installées (--user)"
            } else {
                Write-Host "    ! échec. Relancez : $Py -m pip install --user -r $Reqs" -ForegroundColor Yellow
            }
        }

        # ─── Config utilisateur ───────────────────────────────────
        $Env = Join-Path $Racine ".env"
        $Modele = Join-Path $Racine "config\.env.example"
        if ((-not (Test-Path $Env)) -and (Test-Path $Modele)) {
            Copy-Item $Modele $Env
            Write-Host "  → Modèle de configuration créé : $Env"
        }

        Write-Host ""
        Write-Host "  ✓ Installé." -ForegroundColor Green
        Write-Host ""
        Write-Host "  Prochaine étape — dans Claude Code :"
        Write-Host ""
        Write-Host "      /seo doctor"
        Write-Host ""
        Write-Host "  Il vous dira quoi brancher, dans quel ordre, et lancera"
        Write-Host "  la première action utile."
        Write-Host ""
        Write-Host "  Configuration : $Env"
        Write-Host "  Documentation : $Racine\docs\"
        Write-Host ""
    }
    finally {
        Remove-Item -Recurse -Force $Tempo -ErrorAction SilentlyContinue
    }
}

Install-SeoDecupler
