<#
.SYNOPSIS
Regénère les trois essais de terrain, puis leurs captures à midi et à 22 h.
#>
[CmdletBinding()]
param(
    [string]$EnginePath = 'E:\Epic Games\UE_5.8',
    [string]$BlenderPath = 'D:\Blender Foundation\Blender 5.2\blender.exe',
    [switch]$SkipPrepare,
    [switch]$SkipBuild,
    [switch]$SkipCapture,
    [switch]$ReuseAssets,
    [switch]$SkipDiagnostics
)
throw 'Pipeline historique archive : ouvrir Capitale. Ne pas regenerer les anciennes cartes d essai.'
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$project = Join-Path $root 'JustAnotherRpgGame.uproject'
$python = Join-Path $root '.venv\Scripts\python.exe'
$editor = Join-Path $EnginePath 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$reports = Join-Path $root 'Saved\Jadg\capital-terrain-labs'
$cache = (Join-Path $root 'Saved\DerivedDataCache') -replace '\\','/'
$cacheArgs = @("-ZenDataPath=$cache/Zen", "-LocalDataCachePath=$cache", '-noxgeshadercompile')
$names = @('capitale-sols-urbains','capitale-rives','capitale-terres-roches')
New-Item -ItemType Directory -Force -Path $reports | Out-Null
if (Get-Process -Name UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue) {
    throw 'Une instance Unreal est ouverte ; ne pas construire deux mondes en parallèle.'
}
Push-Location $root
try {
    if (-not $SkipPrepare) {
        & $BlenderPath --background --python (Join-Path $root 'scripts/assetsGeneration/build_capital_terrain_modules.py') *> (Join-Path $reports 'meshes.log')
        if ($LASTEXITCODE -ne 0) { throw 'Génération des meshes échouée.' }
        & $python 'scripts/maps/build_capital_terrain_labs.py' --prepare
        if ($LASTEXITCODE -ne 0) { throw 'Préparation des terrains échouée.' }
        & $python 'scripts/maps/jadg_map.py' --check essai/capitale-sols-urbains essai/capitale-rives essai/capitale-terres-roches
        if ($LASTEXITCODE -ne 0) { throw 'Descriptions de cartes invalides.' }
    }
    if (-not $SkipBuild) {
        $started = Get-Date
        $script = (Join-Path $root 'scripts/maps/build_capital_terrain_labs.py') -replace '\\','/'
        $reuseArgs = if ($ReuseAssets) { @('-JadgLabsReuseAssets') } else { @() }
        & $editor $project -run=pythonscript "-script=$script" @cacheArgs @reuseArgs -unattended -nosplash -nullrhi -NoSound -stdout -FullStdOutLogOutput *> (Join-Path $reports 'build.log')
        if ($LASTEXITCODE -ne 0) { throw 'Construction échouée : voir Saved/Jadg/capital-terrain-labs/build.log.' }
        if (-not (Test-Path (Join-Path $reports 'build.json')) -or (Get-Item (Join-Path $reports 'build.json')).LastWriteTime -lt $started) { throw 'Rapport de construction absent ou ancien.' }
    }
    if (-not $SkipCapture) {
        $audit = (Join-Path $root 'scripts/maps/audit_capital_terrain_labs.py') -replace '\\','/'
        & $editor $project -run=pythonscript "-script=$audit" @cacheArgs -unattended -nosplash -nullrhi -NoSound -stdout -FullStdOutLogOutput *> (Join-Path $reports 'audit.log')
        if ($LASTEXITCODE -ne 0) { throw 'Audit des cartes sauvegardées échoué.' }
        foreach ($name in $names) {
            $output = Join-Path $root "Saved/Captures/capital-terrain-labs/$name"
            New-Item -ItemType Directory -Force -Path $output | Out-Null
            $started = Get-Date
            $log = Join-Path $reports "$name-capture.log"
            & $editor $project "/Game/Maps/Levels/essai/$name" @cacheArgs -game -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound "-JadgCapture=$output" '-JadgHours=12:00,22:00' -JadgSettle=180 -JadgMeasure=4 -stdout -FullStdOutLogOutput *> $log
            if ($LASTEXITCODE -ne 0) { throw "Capture échouée : $name" }
            if (Select-String -LiteralPath $log -Pattern 'Failed to compile Material|LogPython: Error' -Quiet) { throw "Matière invalide : $name" }
            $doc = Get-Content -Raw -LiteralPath "Source/Test/Fixtures/Exploration/Levels/essai/$name.json" | ConvertFrom-Json
            foreach ($shot in $doc.shots) {
                foreach ($hour in @('1200','2200')) {
                    $file = Join-Path $output "$($shot.id)-$hour.png"
                    if (-not (Test-Path -LiteralPath $file) -or (Get-Item -LiteralPath $file).LastWriteTime -lt $started) { throw "Capture absente : $file" }
                }
            }
            Write-Output "Captures contrôlées : $name"
        }
        if (-not $SkipDiagnostics) {
            foreach ($mode in @('Mask','Triangles')) {
                $output = Join-Path $root "Saved/Captures/capital-terrain-labs/Nanite-$mode"
                New-Item -ItemType Directory -Force -Path $output | Out-Null
                $log = Join-Path $reports "nanite-$mode.log"
                & $editor $project '/Game/Maps/Levels/essai/capitale-sols-urbains' @cacheArgs -game -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound "-JadgCapture=$output" '-JadgHours=12:00' '-JadgShots=ensemble' "-ExecCmds=viewmode visualizenanite,r.Nanite.Visualize $mode" -JadgSettle=180 -stdout -FullStdOutLogOutput *> $log
                if ($LASTEXITCODE -ne 0) { throw "Diagnostic Nanite échoué : $mode" }
                if (Select-String -LiteralPath $log -Pattern 'view mode not recognized|Debug viewmodes not allowed|Unknown Nanite visualization|Failed to compile Material' -Quiet) { throw "Diagnostic Nanite non actif : $mode" }
            }
        }
    }
} finally { Pop-Location }
