<#
.SYNOPSIS
    Vérifie, et sur demande installe, les outils du poste aux versions exactes de la CI.

.DESCRIPTION
    Le fil de ci.yml est qu'un contrôle qui ne prédit pas le résultat local ne sert à rien. Ce script
    en tire la conséquence pour le poste (refonte de la chaîne d'outillage, phase 2) : il ne porte
    AUCUNE version. Il lit le bloc `env:` de .github/workflows/ci.yml et compare ce qui est installé
    à ce que le runner installe. Monter un outil se fait donc dans ci.yml, et nulle part ailleurs.

    Sans paramètre, il ne modifie rien : il affiche un tableau (outil, version attendue, version
    trouvée) et échoue si un écart existe. Avec -Install, il installe ce qui manque ou diverge :
      - pip (lanceur `py`) pour pre-commit, clang-format et uv ;
      - le paquet de la PowerShell Gallery pour PSScriptAnalyzer, dans les modules de l'utilisateur ;
    puis crée l'environnement Python du dépôt (`uv sync --locked`, versions de uv.lock) et installe
    les hooks de .pre-commit-config.yaml dans le clone courant.

    Ne sont que vérifiés, jamais installés : Visual Studio (outils C++ x64) et Unreal Engine, trop
    lourds et trop personnels pour un script. Pour le moteur, la version attendue est
    `UNREAL_ENGINE_VERSION` ; il est cherché comme `scripts/build.ps1 -Unreal` le cherche (par
    l'association du .uproject dans le registre), ou sous -EnginePath.

.PARAMETER Install
    Installer ou mettre à niveau ce qui ne correspond pas à ci.yml. Accepte -WhatIf.

.PARAMETER EnginePath
    Racine d'une installation du moteur (ex. « E:\Epic Games\UE_5.8 »), si le registre ne la
    donne pas.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts/setup_dev.ps1
    Diagnostic seul.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts/setup_dev.ps1 -Install -WhatIf
    Affiche ce qui serait installé, sans rien installer.
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [switch]$Install,
    [string]$EnginePath
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$ciPath = Join-Path $repoRoot '.github\workflows\ci.yml'

# --- Versions de la CI --------------------------------------------------------------------------

function Read-CiEnv {
    param([string]$Path)
    $values = @{}
    $inEnv = $false
    foreach ($line in [System.IO.File]::ReadAllLines($Path)) {
        if ($line -match '^env:\s*$') { $inEnv = $true; continue }
        if ($inEnv -and $line -match '^\S') { break }
        if ($inEnv -and $line -match "^  ([A-Z0-9_]+):\s*['""]?([^'""\s#]+)") {
            $values[$Matches[1]] = $Matches[2]
        }
    }
    return $values
}

$ci = Read-CiEnv $ciPath
$required = 'LLVM_VERSION', 'UV_VERSION', 'PSSCRIPTANALYZER_VERSION', 'PRE_COMMIT_VERSION',
            'UNREAL_ENGINE_VERSION'
foreach ($name in $required) {
    if (-not $ci.ContainsKey($name)) {
        throw "$name introuvable dans le bloc env: de $ciPath : la lecture est à corriger."
    }
}

# --- Détection ----------------------------------------------------------------------------------

# Premier nombre x.y[.z[.w]] d'une sortie de commande, ou $null.
function Get-VersionFrom {
    param([string[]]$Text)
    foreach ($line in $Text) {
        if ("$line" -match '(\d+\.\d+(\.\d+){0,2})') { return $Matches[1] }
    }
    return $null
}

function Invoke-Quiet {
    param([string]$Exe, [string[]]$Arguments)
    try {
        $previous = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        $output = & $Exe @Arguments 2>$null
        $ErrorActionPreference = $previous
        if ($LASTEXITCODE -ne 0) { return $null }
        return $output
    }
    catch {
        $ErrorActionPreference = $previous
        return $null
    }
}

function Find-Exe {
    param([string]$Name, [string[]]$Candidates = @())
    foreach ($path in $Candidates) {
        if ($path -and (Test-Path $path)) { return $path }
    }
    $command = Get-Command $Name -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($command) { return $command.Source }
    return $null
}

# Le lanceur `py` choisit un CPython installé ; `python` du PATH peut être n'importe quoi (celui
# d'Inkscape ou de GIMP s'y glisse souvent) et n'est donc jamais utilisé pour installer.
$py = Find-Exe 'py'
function Get-PipVersion {
    param([string]$Package)
    if (-not $py) { return $null }
    $output = Invoke-Quiet $py @('-3', '-m', 'pip', 'show', $Package)
    foreach ($line in $output) {
        if ("$line" -match '^Version:\s*(\S+)') { return $Matches[1] }
    }
    return $null
}

$tools = @(
    # Pour un outil qui a un exécutable, c'est la version de l'exécutable APPELÉ qui compte : avec
    # plusieurs Python installés, pip peut répondre pour un autre que celui du PATH.
    [pscustomobject]@{
        Name = 'pre-commit'; Expected = $ci.PRE_COMMIT_VERSION; Kind = 'pip'; Package = 'pre-commit'
        Detect = {
            $exe = Find-Exe 'pre-commit'
            if ($exe) { Get-VersionFrom (Invoke-Quiet $exe @('--version')) }
            elseif ($py) { Get-VersionFrom (Invoke-Quiet $py @('-3', '-m', 'pre_commit', '--version')) }
        }
    },
    # Les dépendances Python des scripts (jsonschema, pytest, Pillow) ne sont pas listées : elles
    # sont dans uv.lock, et `uv sync --locked` les installe à l'identique en fin de -Install.
    [pscustomobject]@{
        Name = 'uv'; Expected = $ci.UV_VERSION; Kind = 'pip'; Package = 'uv'
        Detect = {
            $exe = Find-Exe 'uv'
            if ($exe) { Get-VersionFrom (Invoke-Quiet $exe @('--version')) }
            else { Get-PipVersion 'uv' }
        }
    },
    [pscustomobject]@{
        Name = 'PSScriptAnalyzer'; Expected = $ci.PSSCRIPTANALYZER_VERSION; Kind = 'psgallery'; Package = 'PSScriptAnalyzer'
        Detect = {
            $module = Get-Module -ListAvailable PSScriptAnalyzer |
                Where-Object { $_.Version -eq [version]$ci.PSSCRIPTANALYZER_VERSION } | Select-Object -First 1
            if ($module) { "$($module.Version)" }
        }
    },
    [pscustomobject]@{
        Name = 'clang-format'; Expected = $ci.LLVM_VERSION; Kind = 'pip'; Package = 'clang-format'
        Detect = {
            $exe = Find-Exe 'clang-format'
            if ($exe) { Get-VersionFrom (Invoke-Quiet $exe @('--version')) }
        }
    }
)

function Test-VersionMatch {
    param([string]$Expected, [string]$Found)
    if (-not $Found) { return $false }
    # Un outil rapporte 1.2.3.0 ou 1.2.3 selon la source : on compare les composantes lues.
    $e = $Expected.Split('.'); $f = $Found.Split('.')
    for ($i = 0; $i -lt [Math]::Max($e.Count, $f.Count); $i++) {
        $a = if ($i -lt $e.Count) { $e[$i] } else { '0' }
        $b = if ($i -lt $f.Count) { $f[$i] } else { '0' }
        if ($a -ne $b) { return $false }
    }
    return $true
}

# --- Installation -------------------------------------------------------------------------------

function Install-Tool {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param($Tool)
    switch ($Tool.Kind) {
        'pip' {
            if (-not $py) { throw "Le lanceur Python « py » est introuvable : installer Python 3.12 ou plus (python.org)." }
            $spec = "$($Tool.Package)==$($Tool.Expected)"
            if ($PSCmdlet.ShouldProcess($spec, 'py -3 -m pip install')) {
                & $py -3 -m pip install --disable-pip-version-check $spec
                if ($LASTEXITCODE -ne 0) { throw "pip install $spec : échec ($LASTEXITCODE)." }
            }
        }
        'psgallery' {
            # Le paquet est un zip : l'extraire dans les modules de l'utilisateur évite
            # Install-Module, qui exige sous Windows PowerShell 5.1 le fournisseur NuGet, installé
            # pour toute la machine.
            $version = $Tool.Expected
            $url = "https://www.powershellgallery.com/api/v2/package/$($Tool.Package)/$version"
            $modules = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'WindowsPowerShell\Modules'
            $target = Join-Path $modules "$($Tool.Package)\$version"
            if ($PSCmdlet.ShouldProcess($url, "Extraire dans $target")) {
                $zip = Join-Path $env:TEMP "$($Tool.Package).$version.zip"
                [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
                Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $zip
                Expand-Archive $zip $target -Force
            }
        }
    }
}

# --- Diagnostic ---------------------------------------------------------------------------------

$rows = @()
$mismatches = @()
foreach ($tool in $tools) {
    $found = & $tool.Detect
    $ok = Test-VersionMatch $tool.Expected $found
    if (-not $ok) { $mismatches += $tool }
    $rows += [pscustomobject]@{
        Outil     = $tool.Name
        Attendue  = $tool.Expected
        Trouvee   = $(if ($found) { $found } else { '-' })
        Verdict   = $(if ($ok) { 'OK' } else { 'ECART' })
    }
}

# Visual Studio et Unreal Engine : vérifiés, jamais installés.
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
$vsPath = $null
if (Test-Path $vswhere) {
    $vsPath = & $vswhere -latest -prerelease -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
}
$rows += [pscustomobject]@{ Outil = 'Visual Studio (C++ x64)'; Attendue = '2022+'
    Trouvee = $(if ($vsPath) { $vsPath } else { '-' }); Verdict = $(if ($vsPath) { 'OK' } else { 'A INSTALLER' }) }

# Le moteur : celui que le .uproject associe (registre de l'utilisateur, puis de la machine), comme
# `scripts/build.ps1 -Unreal` le cherche ; sa version est lue dans Engine/Build/Build.version.
if (-not $EnginePath) {
    $association = (Get-Content (Join-Path $repoRoot 'JustAnotherRpgGame.uproject') -Raw | ConvertFrom-Json).EngineAssociation
    $builds = Get-ItemProperty 'HKCU:\Software\Epic Games\Unreal Engine\Builds' -ErrorAction SilentlyContinue
    if ($builds -and $builds.PSObject.Properties[$association]) {
        $EnginePath = $builds.PSObject.Properties[$association].Value
    }
    if (-not $EnginePath) {
        $installed = Get-ItemProperty "HKLM:\SOFTWARE\EpicGames\Unreal Engine\$association" -ErrorAction SilentlyContinue
        if ($installed) { $EnginePath = $installed.InstalledDirectory }
    }
}
$engineFound = $null
if ($EnginePath) {
    $versionFile = Join-Path $EnginePath 'Engine\Build\Build.version'
    if (Test-Path $versionFile) {
        $engine = Get-Content $versionFile -Raw | ConvertFrom-Json
        $engineFound = "$($engine.MajorVersion).$($engine.MinorVersion)"
    }
}
$engineOk = $engineFound -eq $ci.UNREAL_ENGINE_VERSION
$rows += [pscustomobject]@{ Outil = 'Unreal Engine'; Attendue = $ci.UNREAL_ENGINE_VERSION
    Trouvee = $(if ($engineFound) { "$engineFound ($EnginePath)" } else { '-' })
    Verdict = $(if ($engineOk) { 'OK' } elseif ($engineFound) { 'ECART' } else { 'A INSTALLER (ou -EnginePath)' }) }

Write-Host "Versions lues dans $ciPath" -ForegroundColor DarkGray
$rows | Format-Table -AutoSize | Out-String -Width 200 | Write-Host

$pythonOnPath = Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pythonOnPath -and $pythonOnPath.Source -notmatch '\\Python3\d+\\|\\WindowsApps\\|\\py\.exe$') {
    Write-Warning ("« python » du PATH est $($pythonOnPath.Source), qui n'est pas une installation CPython " +
        "standard. Les scripts s'exécutent avec « py -3 scripts/... » ; pre-commit crée ses propres environnements.")
}

if (-not $Install) {
    if ($mismatches.Count -gt 0) {
        Write-Host "$($mismatches.Count) écart(s). Installer aux versions de la CI : scripts/setup_dev.ps1 -Install" -ForegroundColor Yellow
        exit 1
    }
    Write-Host 'Poste aligné sur la CI.' -ForegroundColor Green
    exit 0
}

foreach ($tool in $mismatches) {
    Write-Host "==> $($tool.Name) $($tool.Expected)" -ForegroundColor Cyan
    Install-Tool $tool
}

# L'environnement Python des scripts, aux versions de uv.lock (celles du runner).
if ($PSCmdlet.ShouldProcess($repoRoot, 'uv sync --locked (.venv)')) {
    Push-Location $repoRoot
    try {
        $uv = Find-Exe 'uv'
        if ($uv) { & $uv sync --locked } else { & $py -3 -m uv sync --locked }
        if ($LASTEXITCODE -ne 0) { throw "uv sync --locked : échec ($LASTEXITCODE)." }
    }
    finally {
        Pop-Location
    }
}

# Les images des kits d'assets, hors de Git (LOT-108) : téléchargées d'après kits.lock.json, dans
# un cache partagé par les clones et worktrees du poste (%LOCALAPPDATA%\JadgAssets).
if ($PSCmdlet.ShouldProcess($repoRoot, 'scripts/fetch_assets.py (kits d''assets)')) {
    Push-Location $repoRoot
    try {
        & $py -3 scripts/fetch_assets.py
        if ($LASTEXITCODE -ne 0) { throw "fetch_assets.py : échec ($LASTEXITCODE)." }
    }
    finally {
        Pop-Location
    }
}

# Les hooks s'installent par clone ET par worktree : chacun a son propre dossier .git/hooks effectif.
if ($PSCmdlet.ShouldProcess($repoRoot, 'pre-commit install (hooks pre-commit et commit-msg)')) {
    Push-Location $repoRoot
    try {
        $preCommit = Find-Exe 'pre-commit'
        if ($preCommit) { & $preCommit install } else { & $py -3 -m pre_commit install }
        if ($LASTEXITCODE -ne 0) { throw "pre-commit install : échec ($LASTEXITCODE)." }
    }
    finally {
        Pop-Location
    }
}
Write-Host 'Terminé. Ouvrir un nouveau terminal pour que le PATH mis à jour soit pris en compte.' -ForegroundColor Green
