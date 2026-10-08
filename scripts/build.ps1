<#
.SYNOPSIS
    Construit et vérifie JustAnotherRpgGame sans ouvrir une fenêtre (LOT-1014).

.DESCRIPTION
    Deux constructions, une règle : sortir en 1 à la première erreur.

    - Par défaut, les tests de Core HORS du moteur : CMake + Ninja + GoogleTest sur
      Source/JustAnotherRpgGame/Core, dans un environnement MSVC x64 que le script établit lui-même
      (vswhere, puis vcvars64.bat : une « Developer PowerShell » démarre en x86).
    - Avec -Unreal, le projet du moteur : UnrealBuildTool construit la cible d'éditeur, puis
      UnrealEditor-Cmd lance le commandlet JadgContentCheck, qui lit les données de contenu par les
      lecteurs de Core et compte ses erreurs. Le moteur est trouvé par l'association du .uproject
      (registre HKCU\Software\Epic Games\Unreal Engine\Builds), ou par -EnginePath.

.PARAMETER Unreal
    Construire le projet Unreal et lancer le commandlet de contrôle du contenu.

.PARAMETER EnginePath
    Racine d'une installation du moteur (ex. « E:\Epic Games\UE_5.8 »), si le registre ne la
    donne pas.

.PARAMETER Configuration
    Configuration UnrealBuildTool : Development (défaut), DebugGame ou Debug.

.PARAMETER Preset
    Preset CMake des tests de Core : « ninja » (Debug, défaut) ou « ninja-release ».

.PARAMETER Clean
    Supprimer le répertoire de build CMake avant de configurer (sans effet sur le moteur).

.EXAMPLE
    pwsh scripts/build.ps1
    Construit Core et lance ses tests GoogleTest.

.EXAMPLE
    pwsh scripts/build.ps1 -Unreal
    Construit l'éditeur du projet et vérifie le contenu, sans fenêtre.
#>
[CmdletBinding()]
param(
    [switch]$Unreal,
    [string]$EnginePath,
    [ValidateSet('Development', 'DebugGame', 'Debug')]
    [string]$Configuration = 'Development',
    [ValidateSet('ninja', 'ninja-release')]
    [string]$Preset = 'ninja',
    [switch]$Clean
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$uproject = Join-Path $root 'JustAnotherRpgGame.uproject'

function Fail([string]$message) {
    Write-Error $message
    exit 1
}

function Find-VisualStudio {
    $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    if (-not (Test-Path $vswhere)) { Fail "vswhere.exe introuvable : Visual Studio n'est pas installé." }
    $path = & $vswhere -latest -prerelease -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    if (-not $path) { Fail 'Aucune installation de Visual Studio avec les outils C++ x64.' }
    return $path
}

function Invoke-InMsvcEnvironment([string]$vsPath, [string]$commands) {
    $vcvars = Join-Path $vsPath 'VC\Auxiliary\Build\vcvars64.bat'
    $cmakeBin = Join-Path $vsPath 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin'
    $ninjaBin = Join-Path $vsPath 'Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja'
    # vcvars appelle vswhere.exe par son nom : le dossier de l'installateur doit être dans PATH.
    $installer = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer'
    $env:PATH = "$installer;$cmakeBin;$ninjaBin;$env:PATH"
    cmd /c "call `"$vcvars`" >nul && cd /d `"$root`" && $commands"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if ($Unreal) {
    if (-not $EnginePath) {
        $association = (Get-Content $uproject -Raw | ConvertFrom-Json).EngineAssociation
        $builds = Get-ItemProperty 'HKCU:\Software\Epic Games\Unreal Engine\Builds' -ErrorAction SilentlyContinue
        if ($builds -and $builds.PSObject.Properties[$association]) {
            $EnginePath = $builds.PSObject.Properties[$association].Value
        }
        if (-not $EnginePath) {
            $installed = Get-ItemProperty "HKLM:\SOFTWARE\EpicGames\Unreal Engine\$association" -ErrorAction SilentlyContinue
            if ($installed) { $EnginePath = $installed.InstalledDirectory }
        }
        if (-not $EnginePath) { Fail "Moteur « $association » introuvable : passer -EnginePath." }
    }
    $EnginePath = $EnginePath -replace '/', '\'
    $build = Join-Path $EnginePath 'Engine\Build\BatchFiles\Build.bat'
    $editorCmd = Join-Path $EnginePath 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
    foreach ($tool in @($build, $editorCmd)) {
        if (-not (Test-Path $tool)) { Fail "Outil du moteur introuvable : $tool" }
    }

    Write-Host "== UnrealBuildTool : JustAnotherRpgGameEditor Win64 $Configuration ==" -ForegroundColor Cyan
    & $build JustAnotherRpgGameEditor Win64 $Configuration -Project="$uproject" -WaitMutex -NoHotReload
    if ($LASTEXITCODE -ne 0) { Fail "La construction du moteur a échoué (code $LASTEXITCODE)." }

    Write-Host '== Commandlet JadgContentCheck (sans fenêtre) ==' -ForegroundColor Cyan
    & $editorCmd "$uproject" -run=JadgContentCheck -unattended -nosplash -nullrhi -NoSound -stdout -FullStdOutLogOutput
    if ($LASTEXITCODE -ne 0) { Fail "Le contrôle du contenu a échoué (code $LASTEXITCODE)." }
    exit 0
}

$vs = Find-VisualStudio
$binaryDir = Join-Path $root "build\$Preset"
if ($Clean -and (Test-Path $binaryDir)) { Remove-Item -Recurse -Force $binaryDir }

Write-Host "== Tests de Core hors moteur : preset $Preset (Visual Studio : $vs) ==" -ForegroundColor Cyan
Invoke-InMsvcEnvironment $vs "cmake --preset $Preset && cmake --build --preset $Preset && ctest --preset $Preset"
exit 0
