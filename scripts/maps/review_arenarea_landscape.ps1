<#
.SYNOPSIS
Construit Arenarea, un quartier à la fois, en phases indépendantes et vérifiables.
#>
[CmdletBinding()]
param(
    [ValidateSet('All','Relief','Materials','Foliage','Review')][string]$Phase = 'All',
    [string]$EnginePath = 'E:\Epic Games\UE_5.8',
    [string]$BlenderPath = 'D:\Blender Foundation\Blender 5.2\blender.exe',
    [int]$ZenPort = 0,
    [switch]$SkipCapture
)
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$python=Join-Path $root '.venv/Scripts/python.exe'
$editor=Join-Path $EnginePath 'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$project=Join-Path $root 'JustAnotherRpgGame.uproject'
$report=Join-Path $root 'Saved/Jadg/arenarea-landscape'
$script=(Join-Path $root 'scripts/maps/build_arenarea_landscape.py') -replace '\\','/'
$cache=(Join-Path $root 'Saved/DerivedDataCache') -replace '\\','/'
$cacheArgs=@("-ZenDataPath=$cache/Zen","-LocalDataCachePath=$cache",'-noxgeshadercompile','-nowrite')
if($ZenPort -gt 0){$cacheArgs += "-NoZenAutoLaunch=localhost:$ZenPort"}
New-Item -ItemType Directory -Force -Path $report | Out-Null
$previousTemp=$env:TEMP
$previousTmp=$env:TMP
$env:TEMP=Join-Path $report 'Temp'
$env:TMP=$env:TEMP
New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null
if(Get-Process -Name UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue){
    throw 'Une instance Unreal est ouverte : fermer le projet avant la construction.'
}
function Invoke-Phase([string]$Name){
    $renderArgs=if($Name -in @('relief','materials')){@('-AllowCommandletRendering','-RenderOffscreen')}else{@('-nullrhi')}
    & $editor $project -run=pythonscript "-script=$script" "-JadgArenareaPhase=$Name" @cacheArgs @renderArgs -unattended -nosplash -NoSound -stdout -FullStdOutLogOutput *> (Join-Path $report "$Name.log")
    if($LASTEXITCODE -ne 0){throw "Phase Arenarea échouée : $Name"}
    Write-Output "Phase Arenarea terminée : $Name"
}
Push-Location $root
try{
    if($Phase -in @('All','Relief')){
        & $python 'scripts/maps/prepare_arenarea_landscape.py'
        if($LASTEXITCODE -ne 0){throw 'Préparation du relief échouée.'}
        & $python 'scripts/maps/jadg_map.py' --check capital-landscape/arenarea
        if($LASTEXITCODE -ne 0){throw 'Description de carte invalide.'}
        & $BlenderPath --background --python (Join-Path $root 'scripts/assetsGeneration/build_arenarea_water.py') *> (Join-Path $report 'water.log')
        if($LASTEXITCODE -ne 0){throw "Surface d'eau échouée."}
        Invoke-Phase 'relief'
    }
    if($Phase -in @('All','Materials')){Invoke-Phase 'materials'}
    if($Phase -in @('All','Foliage')){
        $inventory=(Join-Path $root 'scripts/maps/inspect_arenarea_fab.py') -replace '\\','/'
        & $editor $project -run=pythonscript "-script=$inventory" @cacheArgs -unattended -nosplash -nullrhi -NoSound -stdout -FullStdOutLogOutput *> (Join-Path $report 'fab-inventory.log')
        if($LASTEXITCODE -ne 0){throw 'Inventaire Fab échoué.'}
        & $python 'scripts/maps/prepare_arenarea_foliage.py'
        if($LASTEXITCODE -ne 0){throw 'Plantation échouée.'}
        Invoke-Phase 'foliage'
    }
    if($Phase -in @('All','Review')){
        Invoke-Phase 'audit'
        if(-not $SkipCapture){
            $output=Join-Path $root 'Saved/Captures/arenarea-landscape'
            New-Item -ItemType Directory -Force -Path $output | Out-Null
            $start=Get-Date
            & $editor $project '/Game/Maps/Levels/capital-landscape/arenarea' @cacheArgs -game -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound "-JadgCapture=$output" '-JadgHours=12:00,22:00' -JadgSettle=180 -JadgMeasure=4 -stdout -FullStdOutLogOutput *> (Join-Path $report 'capture.log')
            if($LASTEXITCODE -ne 0){throw 'Captures Arenarea échouées.'}
            if(Select-String -LiteralPath (Join-Path $report 'capture.log') -Pattern 'Failed to compile Material|Fatal error' -Quiet){throw 'Erreur de rendu.'}
            foreach($shot in @('parvis','jardins','natural-pool','rive','prairie')){
                foreach($hour in @('1200','2200')){
                    $file=Join-Path $output "$shot-$hour.png"
                    if(-not(Test-Path -LiteralPath $file) -or (Get-Item -LiteralPath $file).LastWriteTime -lt $start){throw "Capture absente : $file"}
                }
            }
            Write-Output 'Dix captures Arenarea contrôlées.'
        }
    }
} finally {
    Pop-Location
    $env:TEMP=$previousTemp
    $env:TMP=$previousTmp
}
