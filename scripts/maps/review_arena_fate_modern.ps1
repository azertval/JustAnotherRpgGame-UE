<#
.SYNOPSIS
    Régénère, parcourt et capture l'arène complète peinte, sans fenêtre.
.DESCRIPTION
    L'ancien JSON et les cartes natives sont archivés sous Saved avant remplacement.
    Géométrie et props utilisent les matières du témoin approuvé, sans foule provisoire.
    Les étapes Unreal sont séquentielles. Ce script ne doit pas tourner avec un autre éditeur.
#>
[CmdletBinding()]
param(
    [string]$EnginePath = 'E:\Epic Games\UE_5.8',
    [switch]$Generate,
    [switch]$Compile,
    [switch]$SkipBuild,
    [switch]$SkipCapture,
    [switch]$Walk,
    [int]$MeasureSeconds = 10
)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$uproject = Join-Path $projectRoot 'JustAnotherRpgGame.uproject'
$editor = Join-Path $EnginePath 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$reports = Join-Path $projectRoot 'Saved\Jadg\arena-fate-modern'
$logs = Join-Path $reports 'logs'
$package = '/Game/Maps/Levels/central-empire/capital/arenarea/arena-of-fate'
New-Item -ItemType Directory -Path $logs -Force | Out-Null
foreach ($required in @($python, $uproject, $editor)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Absent : $required" }
}
if ($MeasureSeconds -lt 1) { throw 'La mesure doit durer au moins une seconde.' }
Push-Location $projectRoot
try {
    if ($Generate) {
        foreach ($generator in @('build_arena_witness_textures.py', 'build_arena_fate_modern.py', 'build_arena_fate_props.py', 'build_arena_fate_atmosphere.py')) {
            & $python (Join-Path 'scripts\assetsGeneration' $generator)
            if ($LASTEXITCODE -ne 0) { throw "Échec de la géométrie : $generator" }
        }
    }
    if ($Compile) {
        & (Join-Path $EnginePath 'Engine\Build\BatchFiles\Build.bat') JustAnotherRpgGameEditor Win64 Development "-Project=$uproject" -WaitMutex -NoHotReload
        if ($LASTEXITCODE -ne 0) { throw 'Échec de la compilation.' }
    }
    & $python 'scripts\maps\build_arena_fate_modern_scene.py' --prepare
    if ($LASTEXITCODE -ne 0) { throw 'Échec de la description proposée.' }
    if (-not $SkipBuild) {
        $builder = (Join-Path $PSScriptRoot 'build_arena_fate_modern_scene.py') -replace '\\', '/'
        $buildLog = Join-Path $logs 'build.log'
        $buildStarted = Get-Date
        & $editor $uproject -run=pythonscript "-script=$builder" -unattended -nosplash -nullrhi -NoSound -stdout -FullStdOutLogOutput *> $buildLog
        if ($LASTEXITCODE -ne 0) { Get-Content -Tail 65 $buildLog; throw "Construction échouée : $buildLog" }
        $buildReportPath = Join-Path $reports 'build.json'
        if (-not (Test-Path -LiteralPath $buildReportPath) -or (Get-Item -LiteralPath $buildReportPath).LastWriteTime -lt $buildStarted) {
            throw 'Rapport de construction absent ou ancien.'
        }
        $buildReport = Get-Content -Raw $buildReportPath | ConvertFrom-Json
        if (-not $buildReport.sourceCommitted -or @($buildReport.unreachableRouteIndices).Count -gt 0 -or @($buildReport.unreachableTargetIndices).Count -gt 0 -or @($buildReport.missingNavigationAtFloor).Count -gt 0) {
            throw 'La carte et ses trajets ne sont pas validés.'
        }
    }
    if ($Walk) {
        $expectedBuild = Get-Content -Raw (Join-Path $reports 'build.json') | ConvertFrom-Json
        if (-not $expectedBuild.sourceCommitted -or @($expectedBuild.unreachableRouteIndices).Count -gt 0 -or @($expectedBuild.unreachableTargetIndices).Count -gt 0 -or @($expectedBuild.missingNavigationAtFloor).Count -gt 0) {
            throw 'Le parcours physique exige une construction validée, y compris toutes les cibles de navigation.'
        }
        $expectedRouteCount = @($expectedBuild.route).Count
        if ($expectedRouteCount -lt 2) { throw 'Parcours de référence absent ou incomplet.' }
        $expectedWalkPoints = 2 * $expectedRouteCount
        $walkReport = Join-Path $reports 'walk.json'
        $walkLog = Join-Path $logs 'walk.log'
        $walkStarted = Get-Date
        & $editor $uproject $package -game -JadgSansTitre -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound "-JadgWitnessWalk=$walkReport" -stdout -FullStdOutLogOutput *> $walkLog
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $walkReport)) {
            Get-Content -Tail 65 $walkLog
            throw "Parcours physique échoué : $walkLog"
        }
        $walkResult = Get-Content -Raw $walkReport | ConvertFrom-Json
        if ((Get-Item -LiteralPath $walkReport).LastWriteTime -lt $walkStarted -or -not $walkResult.completed -or -not $walkResult.'return' -or $walkResult.pointsReached -ne $walkResult.pointsPlanned -or $walkResult.pointsPlanned -ne $expectedWalkPoints) {
            throw "Parcours non validé : $($walkResult.reason)"
        }
        Write-Output "Parcours : $($walkResult.pointsReached) points atteints, aller-retour."
    }
    if (-not $SkipCapture) {
        $output = Join-Path $projectRoot 'Saved\Captures\arena-fate-modern'
        New-Item -ItemType Directory -Path $output -Force | Out-Null
        $captureLog = Join-Path $logs 'capture.log'
        $captureStarted = Get-Date
        & $editor $uproject $package -game -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound "-JadgCapture=$output" '-JadgHours=12:00,22:00' "-JadgMeasure=$MeasureSeconds" -JadgSettle=90 -stdout -FullStdOutLogOutput *> $captureLog
        if ($LASTEXITCODE -ne 0) { Get-Content -Tail 65 $captureLog; throw "Capture échouée : $captureLog" }
        $doc = Get-Content -Raw (Join-Path $projectRoot 'Source\Elements\Levels\central-empire\capital\arenarea\arena-of-fate.json') | ConvertFrom-Json
        foreach ($shot in $doc.shots) {
            foreach ($hour in @('1200', '2200')) {
                $image = Join-Path $output "$($shot.id)-$hour.png"
                if (-not (Test-Path -LiteralPath $image) -or (Get-Item -LiteralPath $image).LastWriteTime -lt $captureStarted) {
                    throw "Capture absente ou ancienne : $image"
                }
            }
        }
        $measure = Join-Path $output 'mesure.json'
        if (-not (Test-Path -LiteralPath $measure) -or (Get-Item -LiteralPath $measure).LastWriteTime -lt $captureStarted) {
            throw 'Mesure absente ou ancienne.'
        }
        $result = Get-Content -Raw $measure | ConvertFrom-Json
        foreach ($sample in $result.measures) {
            Write-Output "Performance $($sample.hour) : $([math]::Round($sample.fps, 1)) fps, p99 $([math]::Round($sample.p99FrameMs, 2)) ms. Cible : 60 fps en 1080p."
        }
        Write-Output "Captures : $output"
    }
} finally {
    Pop-Location
}
