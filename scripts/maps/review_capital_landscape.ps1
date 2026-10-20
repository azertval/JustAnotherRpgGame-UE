<#
.SYNOPSIS
    Régénère le paysage de la capitale impériale et prend ses captures, à midi et à 22 h.
.DESCRIPTION
    Trois temps, un seul processus Unreal à la fois :
      1. le relief et les couches, hors du moteur (build_capital_landscape_scene.py --prepare) ;
      2. le niveau, dans l'éditeur sans fenêtre (/Game/Maps/Levels/capital-landscape/ensemble) ;
      3. le jeu hors écran sur ce niveau : chaque cadrage de la carte, aux deux heures, et la cadence.
    Sorties : Saved/Jadg/capital-landscape/ (images du relief, rapports, journaux) et
    Saved/Captures/capital-landscape/.
    Inventaire complémentaire des packs : scripts/maps/audit_capital_packs.py,
    à lancer par le commandlet Python de chaque projet source (lecture seule).
#>
[CmdletBinding()]
param(
    [string]$EnginePath = 'E:\Epic Games\UE_5.8',
    [switch]$SkipPrepare,
    [switch]$SkipBuild,
    [switch]$SkipCapture,
    [switch]$SkipMainCaptures,
    [switch]$SkipWitnessCaptures,
    [switch]$SkipBuffers,
    [switch]$SkipRuntimeWalk,
    [switch]$SansNanite,
    [int]$MeasureSeconds = 10
)
throw 'Pipeline historique archive : ouvrir Capitale. Ne pas regenerer les anciennes cartes d essai.'
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$uproject = Join-Path $projectRoot 'JustAnotherRpgGame.uproject'
$editor = Join-Path $EnginePath 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$cacheRoot = (Join-Path $projectRoot 'Saved\DerivedDataCache') -replace '\\', '/'
$cacheArgs = @("-ZenDataPath=$cacheRoot/Zen", "-LocalDataCachePath=$cacheRoot", '-noxgeshadercompile')
$package = '/Game/Maps/Levels/capital-landscape/ensemble'
$reports = Join-Path $projectRoot 'Saved\Jadg\capital-landscape'
$logs = Join-Path $reports 'logs'
foreach ($required in @($python, $uproject, $editor)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Absent : $required" }
}
if (Get-Process -Name UnrealEditor, UnrealEditor-Cmd -ErrorAction SilentlyContinue) {
    throw 'Une instance Unreal est déjà ouverte. La construction doit être séquentielle.'
}
New-Item -ItemType Directory -Path $logs -Force | Out-Null
Push-Location $projectRoot
try {
    if (-not $SkipPrepare) {
        & $python 'scripts\assetsGeneration\install_capital_surface_sources.py'
        if ($LASTEXITCODE -ne 0) { throw 'Surfaces sources indisponibles.' }
        & $python 'scripts\maps\build_capital_landscape_scene.py' --prepare
        if ($LASTEXITCODE -ne 0) { throw 'Relief non préparé.' }
        & $python 'scripts\assetsGeneration\build_capital_urban_assets.py'
        if ($LASTEXITCODE -ne 0) { throw 'Ouvrages et surfaces non préparés.' }
        & $python 'scripts\maps\review_capital_geography.py'
        if ($LASTEXITCODE -ne 0) { throw 'Contrôle géographique échoué.' }
    }
    if (-not $SkipBuild) {
        & (Join-Path $EnginePath 'Engine\Build\BatchFiles\Build.bat') JustAnotherRpgGameEditor Win64 Development "-Project=$uproject" -WaitMutex -NoHotReload *> (Join-Path $logs 'compiler.log')
        if ($LASTEXITCODE -ne 0) { throw 'Compilation des outils de scène échouée.' }
        $script = (Join-Path $projectRoot 'scripts\maps\build_capital_landscape_scene.py') -replace '\\', '/'
        $buildLog = Join-Path $logs 'build.log'
        $buildStarted = Get-Date
        $nanite = if ($SansNanite) { @('-JadgSansNanite') } else { @() }
        & $editor $uproject -run=pythonscript "-script=$script" @cacheArgs @nanite -unattended -nosplash -nullrhi -NoSound -stdout -FullStdOutLogOutput *> $buildLog
        $built = Join-Path $reports 'build.json'
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $built) -or (Get-Item -LiteralPath $built).LastWriteTime -lt $buildStarted) {
            Get-Content -Tail 60 $buildLog
            throw 'Construction du paysage échouée.'
        }
        $report = Get-Content -Raw -LiteralPath $built | ConvertFrom-Json
        Write-Output "Paysage : $($report.quads[0]) x $($report.quads[1]) quads, Nanite $($report.nanite), empreinte $($report.digest.Substring(0, 16))."
    }
    if (-not $SkipCapture) {
        $output = Join-Path $projectRoot 'Saved\Captures\capital-landscape\final'
        New-Item -ItemType Directory -Path $output -Force | Out-Null
        if (-not $SkipMainCaptures) {
        $captureLog = Join-Path $logs 'capture.log'
        $captureStarted = Get-Date
        & $editor $uproject $package @cacheArgs -game -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound "-JadgCapture=$output" '-JadgHours=12:00,22:00' "-JadgMeasure=$MeasureSeconds" -JadgSettle=180 -stdout -FullStdOutLogOutput *> $captureLog
        if ($LASTEXITCODE -ne 0) { Get-Content -Tail 60 $captureLog; throw 'Captures échouées.' }
        if (Select-String -LiteralPath $captureLog -Pattern 'Failed to compile Material' -Quiet) { throw 'Une matière du niveau ne se compile pas dans le jeu.' }
        $doc = Get-Content -Raw -LiteralPath 'Source\Test\Fixtures\Exploration\Levels\capital-landscape\ensemble.json' | ConvertFrom-Json
        foreach ($shot in $doc.shots) {
            foreach ($hour in @('1200', '2200')) {
                $image = Join-Path $output "$($shot.id)-$hour.png"
                if (-not (Test-Path -LiteralPath $image) -or (Get-Item -LiteralPath $image).LastWriteTime -lt $captureStarted) { throw "Capture absente ou ancienne : $image" }
            }
        }
        $measureFile = Join-Path $output 'mesure.json'
        if (Test-Path -LiteralPath $measureFile) {
            foreach ($sample in (Get-Content -Raw -LiteralPath $measureFile | ConvertFrom-Json).measures) {
                Write-Output "$($sample.hour) : $([math]::Round($sample.fps, 1)) images/s ; p99 $([math]::Round($sample.p99FrameMs, 2)) ms."
            }
        }
        foreach ($shotId in @('joueur-water-gate','market-gate-old-bridge','scholarnest-dweomer')) {
            $sampleOutput = Join-Path $output $shotId
            New-Item -ItemType Directory -Path $sampleOutput -Force | Out-Null
            & $editor $uproject $package @cacheArgs -game -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound "-JadgCapture=$sampleOutput" '-JadgHours=12:00,22:00' "-JadgShots=$shotId" "-JadgMeasure=$MeasureSeconds" -JadgSettle=180 -stdout -FullStdOutLogOutput *> (Join-Path $logs "measure-$shotId.log")
            if ($LASTEXITCODE -ne 0) { throw "Mesure échouée : $shotId" }
        }
        }
        $witnessOutput = Join-Path $output 'witness'
        New-Item -ItemType Directory -Path $witnessOutput -Force | Out-Null
        if (-not $SkipWitnessCaptures) {
        $flatOutput = Join-Path $witnessOutput 'displacement-off'
        New-Item -ItemType Directory -Path $flatOutput -Force | Out-Null
        & $editor $uproject '/Game/Maps/Levels/capital-landscape/material-witness' @cacheArgs -game -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound "-JadgCapture=$flatOutput" '-JadgHours=12:00' '-JadgShots=deplacement' '-ini:Engine:[SystemSettings]:r.Nanite.AllowTessellation=0' -JadgSettle=180 -stdout -FullStdOutLogOutput *> (Join-Path $logs 'witness-displacement-off.log')
        if ($LASTEXITCODE -ne 0) { throw 'Capture du témoin sans déplacement échouée.' }
        & $editor $uproject '/Game/Maps/Levels/capital-landscape/material-witness' @cacheArgs -game -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound "-JadgCapture=$witnessOutput" '-JadgHours=12:00,22:00' '-ini:Engine:[SystemSettings]:r.Nanite.AllowTessellation=1' -JadgSettle=180 -stdout -FullStdOutLogOutput *> (Join-Path $logs 'witness-capture.log')
        if ($LASTEXITCODE -ne 0) { throw 'Capture du témoin échouée.' }
        }
        if (-not $SkipBuffers) {
            foreach ($buffer in @('BaseColor','Roughness','WorldNormal','Metallic')) {
                if (-not $SkipWitnessCaptures) {
                $bufferOutput = Join-Path $witnessOutput $buffer
                New-Item -ItemType Directory -Path $bufferOutput -Force | Out-Null
                & $editor $uproject '/Game/Maps/Levels/capital-landscape/material-witness' @cacheArgs -game -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound "-JadgCapture=$bufferOutput" '-JadgHours=12:00' '-JadgShots=atelier' "-ExecCmds=viewmode visualizebuffer,r.BufferVisualizationTarget $buffer" -JadgSettle=180 -stdout -FullStdOutLogOutput *> (Join-Path $logs "buffer-$buffer.log")
                if ($LASTEXITCODE -ne 0) { throw "Buffer du témoin échoué : $buffer" }
                if (Select-String -LiteralPath (Join-Path $logs "buffer-$buffer.log") -Pattern 'view mode not recognized|Debug viewmodes not allowed|Failed to compile Material' -Quiet) { throw "Buffer non actif : $buffer" }
                }
                $cityBufferOutput = Join-Path $output "channels\$buffer"
                New-Item -ItemType Directory -Path $cityBufferOutput -Force | Out-Null
                & $editor $uproject $package @cacheArgs -game -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound "-JadgCapture=$cityBufferOutput" '-JadgHours=12:00' '-JadgShots=proche-palais,proche-universite,proche-arching' "-ExecCmds=viewmode visualizebuffer,r.BufferVisualizationTarget $buffer" -JadgSettle=180 -stdout -FullStdOutLogOutput *> (Join-Path $logs "city-buffer-$buffer.log")
                if ($LASTEXITCODE -ne 0) { throw "Buffer de la capitale échoué : $buffer" }
                if (Select-String -LiteralPath (Join-Path $logs "city-buffer-$buffer.log") -Pattern 'view mode not recognized|Debug viewmodes not allowed|Failed to compile Material' -Quiet) { throw "Buffer de la capitale non actif : $buffer" }
            }
        }
        if (-not $SkipRuntimeWalk) {
            $navigationReport = Join-Path $reports 'navigation-review.json'
            if (-not (Test-Path -LiteralPath $navigationReport)) { throw 'Contrôle de navigation absent avant la marche.' }
            $navigation = Get-Content -Raw -LiteralPath $navigationReport | ConvertFrom-Json
            if (@($navigation.unreachableIndices).Count -gt 0 -or @($navigation.unreachableRuntimeRouteIndices).Count -gt 0 -or @($navigation.strictRuntimeRouteProjectionFailures).Count -gt 0) {
                throw 'Navigation discontinue : corriger les destinations et les projections avant la marche physique.'
            }
            if (@($navigation.runtimeLegs | Where-Object { $_.partial -or -not $_.valid }).Count -gt 0) {
                throw 'Un tronçon du parcours conserve un chemin partiel ou invalide.'
            }
            $walkReport = Join-Path $reports 'runtime-walk.json'
            $walkStarted = Get-Date
            & $editor $uproject $package @cacheArgs -game -JadgSansTitre -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound "-JadgWitnessWalk=$walkReport" -stdout -FullStdOutLogOutput *> (Join-Path $logs 'runtime-walk.log')
            if (-not (Test-Path -LiteralPath $walkReport) -or (Get-Item -LiteralPath $walkReport).LastWriteTime -lt $walkStarted) { throw 'Rapport de marche absent ou ancien.' }
            $walk = Get-Content -Raw -LiteralPath $walkReport | ConvertFrom-Json
            $walk | Add-Member -NotePropertyName sceneDigest -NotePropertyValue ((Get-Content -Raw -LiteralPath (Join-Path $reports 'build.json') | ConvertFrom-Json).digest) -Force
            $walk | Add-Member -NotePropertyName terrainSha256 -NotePropertyValue ((Get-FileHash -LiteralPath (Join-Path $reports 'hauteurs.r16') -Algorithm SHA256).Hash.ToLowerInvariant()) -Force
            $walk | Add-Member -NotePropertyName routeSha256 -NotePropertyValue ((Get-FileHash -LiteralPath (Join-Path $reports 'runtime-route.json') -Algorithm SHA256).Hash.ToLowerInvariant()) -Force
            $walk | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $walkReport -Encoding utf8
            Write-Output "Marche physique : $($walk.pointsReached)/$($walk.pointsPlanned), $($walk.reason)."
            # Preserve the failure evidence and still produce the rendering report.
        }
        $auditScript = (Join-Path $projectRoot 'scripts\maps\audit_capital_landscape.py') -replace '\\', '/'
        & $editor $uproject -run=pythonscript "-script=$auditScript" -JadgAuditAfter @cacheArgs -unattended -nosplash -nullrhi -NoSound -stdout -FullStdOutLogOutput *> (Join-Path $logs 'audit-after.log')
        if ($LASTEXITCODE -ne 0) { throw 'Audit final échoué.' }
        & $python 'scripts\maps\report_capital_review.py'
        if ($LASTEXITCODE -ne 0) { throw 'Rapport final non produit.' }
    }
} finally { Pop-Location }
