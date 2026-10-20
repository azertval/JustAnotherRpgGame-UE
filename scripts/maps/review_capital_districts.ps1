<#
.SYNOPSIS
    Régénère et vérifie Arenarea et Martpart, avec captures Unreal à midi et 22 h.
.DESCRIPTION
    Un seul processus Unreal à la fois. Les sources précédentes et cartes natives
    sont conservées sous Saved/Jadg/districts. La foule est incluse aux mesures.
#>
[CmdletBinding()]
param(
    [string]$EnginePath = 'E:\Epic Games\UE_5.8',
    [ValidateSet('arenarea', 'martpart', 'both')][string]$District = 'both',
    [switch]$Generate,
    [switch]$Compile,
    [switch]$SkipBuild,
    [switch]$SkipCapture,
    [switch]$Walk,
    [int]$MeasureSeconds = 20
)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$uproject = Join-Path $projectRoot 'JustAnotherRpgGame.uproject'
$editor = Join-Path $EnginePath 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$cacheRoot = (Join-Path $projectRoot 'Saved\DerivedDataCache') -replace '\\', '/'
$cacheArgs = @("-ZenDataPath=$cacheRoot/Zen", "-LocalDataCachePath=$cacheRoot", '-noxgeshadercompile')
$selected = if ($District -eq 'both') { @('arenarea', 'martpart') } else { @($District) }
foreach ($required in @($python, $uproject, $editor)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Absent : $required" }
}
if ($MeasureSeconds -lt 1) { throw 'Durée de mesure invalide.' }
if (Get-Process -Name UnrealEditor, UnrealEditor-Cmd -ErrorAction SilentlyContinue) {
    throw 'Une instance Unreal est déjà ouverte. La construction doit être séquentielle.'
}
function Assert-DistrictLife([string]$Path, [datetime]$Started) {
    if (-not (Test-Path -LiteralPath $Path) -or (Get-Item -LiteralPath $Path).LastWriteTime -lt $Started) {
        throw "Rapport de population absent ou ancien : $Path"
    }
    $life = Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
    if (-not $life.ready -or $life.requestedResidents -lt 1 -or $life.spawnedResidents -ne $life.requestedResidents -or $life.rejectedRoutes -ne 0 -or $life.appearanceFailures -ne 0 -or $life.spawnFailures -gt 0) {
        throw "Population incomplète ou routes invalides : $Path"
    }
    foreach ($resident in $life.residents) {
        if (-not $resident.alive -or -not $resident.mutableBody -or -not $resident.animationClips -or $resident.travelledMetres -lt 1 -or $resident.pathRequestsRejected -ne 0) {
            throw "Un passant ne marche pas correctement : $Path"
        }
    }
}
function Assert-NavigationCapacity([string]$Log) {
    if (Select-String -LiteralPath $Log -Pattern 'tile limit reached|Failed to add tile' -Quiet) {
        throw "Navigation tronquée par sa capacité : $Log"
    }
}
function Write-ReviewEvidence([string]$Path, $Built, [datetime]$Started) {
    # Keep review evidence tied to the exact source revision that was exercised.
    [ordered]@{
        manifestSha256 = $Built.manifestSha256
        mapSha256 = $Built.mapSha256
        startedUtc = $Started.ToUniversalTime().ToString('o')
        completedUtc = [datetime]::UtcNow.ToString('o')
    } | ConvertTo-Json | Set-Content -LiteralPath $Path -Encoding utf8
}
Push-Location $projectRoot
try {
    if ($Generate) {
        foreach ($name in $selected) {
            & $python "scripts\assetsGeneration\build_${name}_district.py"
            if ($LASTEXITCODE -ne 0) { throw "Échec Blender : $name" }
        }
    }
    if ($Compile) {
        & (Join-Path $EnginePath 'Engine\Build\BatchFiles\Build.bat') JustAnotherRpgGameEditor Win64 Development "-Project=$uproject" -WaitMutex -NoHotReload
        if ($LASTEXITCODE -ne 0) { throw 'Échec de compilation Unreal.' }
    }
    foreach ($name in $selected) {
        $reports = Join-Path $projectRoot "Saved\Jadg\districts\$name"
        $logs = Join-Path $reports 'logs'
        New-Item -ItemType Directory -Path $logs -Force | Out-Null
        $package = "/Game/Maps/Levels/central-empire/capital/$name"
        if (-not $SkipBuild) {
            & $python 'scripts\maps\build_capital_districts.py' --prepare --district $name
            if ($LASTEXITCODE -ne 0) { throw "Description invalide : $name" }
            $builder = (Join-Path $PSScriptRoot 'build_capital_districts.py') -replace '\\', '/'
            $buildStarted = Get-Date
            $buildLog = Join-Path $logs 'build.log'
            & $editor $uproject @cacheArgs -run=pythonscript "-script=$builder" "-JadgDistrict=$name" -unattended -nosplash -nullrhi -NoSound -stdout -FullStdOutLogOutput *> $buildLog
            if ($LASTEXITCODE -ne 0) { Get-Content -Tail 60 $buildLog; throw "Construction échouée : $name" }
            Assert-NavigationCapacity $buildLog
            $reportFile = Join-Path $reports 'build.json'
            if (-not (Test-Path -LiteralPath $reportFile) -or (Get-Item -LiteralPath $reportFile).LastWriteTime -lt $buildStarted) { throw 'Rapport de construction absent ou ancien.' }
            $built = Get-Content -Raw -LiteralPath $reportFile | ConvertFrom-Json
            if (-not $built.sourceCommitted -or @($built.unreachable).Count -or @($built.missingNavigation).Count) { throw "Navigation non validée : $name" }
        }
        if ($Walk -or -not $SkipCapture) {
            $built = Get-Content -Raw -LiteralPath (Join-Path $reports 'build.json') | ConvertFrom-Json
            $manifest = Join-Path $projectRoot "Source\Elements\Assets\Built\$name-district\manifest.json"
            $mapSource = Join-Path $projectRoot "Source\Elements\Levels\central-empire\capital\$name.json"
            if (-not $built.sourceCommitted -or (Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash -ne $built.manifestSha256 -or (Get-FileHash -LiteralPath $mapSource -Algorithm SHA256).Hash -ne $built.mapSha256) {
                throw "Les sources ont changé depuis la construction de $name. Reconstruire avant la revue."
            }
        }
        if ($Walk) {
            $built = Get-Content -Raw -LiteralPath (Join-Path $reports 'build.json') | ConvertFrom-Json
            if (-not $built.sourceCommitted) { throw 'La carte jouable doit être validée avant le parcours.' }
            $walkFile = Join-Path $reports 'walk.json'
            $walkLog = Join-Path $logs 'walk.log'
            $walkLife = Join-Path $reports 'life-walk.json'
            $walkStarted = Get-Date
            & $editor $uproject $package @cacheArgs -game -JadgSansTitre -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound "-JadgWitnessWalk=$walkFile" "-JadgDistrictLifeReport=$walkLife" -stdout -FullStdOutLogOutput *> $walkLog
            if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $walkFile)) { Get-Content -Tail 60 $walkLog; throw "Parcours échoué : $name" }
            $walked = Get-Content -Raw -LiteralPath $walkFile | ConvertFrom-Json
            if ((Get-Item -LiteralPath $walkFile).LastWriteTime -lt $walkStarted -or -not $walked.completed -or -not $walked.'return' -or $walked.pointsReached -ne $walked.pointsPlanned -or $walked.pointsPlanned -ne (2 * @($built.route).Count)) { throw "Parcours incomplet : $name / $($walked.reason)" }
            Assert-DistrictLife $walkLife $walkStarted
            Assert-NavigationCapacity $walkLog
            Write-ReviewEvidence (Join-Path $reports 'walk-review.json') $built $walkStarted
            Write-Output "$name : $($walked.pointsReached) arrêts atteints, aller-retour."
        }
        if (-not $SkipCapture) {
            $output = Join-Path $projectRoot "Saved\Captures\districts\$name"
            New-Item -ItemType Directory -Path $output -Force | Out-Null
            $captureStarted = Get-Date
            $captureLog = Join-Path $logs 'capture.log'
            $captureLife = Join-Path $reports 'life-capture.json'
            & $editor $uproject $package @cacheArgs -game -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound "-JadgCapture=$output" '-JadgHours=12:00,22:00' "-JadgMeasure=$MeasureSeconds" -JadgSettle=120 "-JadgDistrictLifeReport=$captureLife" -stdout -FullStdOutLogOutput *> $captureLog
            if ($LASTEXITCODE -ne 0) { Get-Content -Tail 60 $captureLog; throw "Captures échouées : $name" }
            Assert-DistrictLife $captureLife $captureStarted
            Assert-NavigationCapacity $captureLog
            $doc = Get-Content -Raw -LiteralPath "Source\Elements\Levels\central-empire\capital\$name.json" | ConvertFrom-Json
            foreach ($shot in $doc.shots) {
                foreach ($hour in @('1200', '2200')) {
                    $image = Join-Path $output "$($shot.id)-$hour.png"
                    if (-not (Test-Path -LiteralPath $image) -or (Get-Item -LiteralPath $image).LastWriteTime -lt $captureStarted) { throw "Capture absente ou ancienne : $image" }
                }
            }
            $measureFile = Join-Path $output 'mesure.json'
            if (-not (Test-Path -LiteralPath $measureFile) -or (Get-Item -LiteralPath $measureFile).LastWriteTime -lt $captureStarted) { throw 'Mesure absente ou ancienne.' }
            $measured = Get-Content -Raw -LiteralPath $measureFile | ConvertFrom-Json
            foreach ($sample in $measured.measures) {
                Write-Output "$name $($sample.hour) : $([math]::Round($sample.fps, 1)) images/s ; p99 $([math]::Round($sample.p99FrameMs, 2)) ms."
            }
            Write-ReviewEvidence (Join-Path $reports 'capture-review.json') $built $captureStarted
        }
    }
    & $python 'scripts\maps\build_capital_districts.py' --gallery
    if ($LASTEXITCODE -ne 0) { throw 'Galerie non produite.' }
} finally { Pop-Location }
