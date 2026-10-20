<#
.SYNOPSIS
Livre les paysages quartier par quartier, sans batiment, puis assemble la capitale.
#>
[CmdletBinding()]
param(
    [ValidateSet('All','Build','Capture','Assemble')][string]$Phase='All',
    [ValidateSet('all','finish')][string]$BuildStage='all',
    [string[]]$Districts=@(),
    [string]$EnginePath='E:\Epic Games\UE_5.8',
    [string]$BlenderPath='D:\Blender Foundation\Blender 5.2\blender.exe',
    [int]$ZenPort=0,
    [switch]$Resume,
    [switch]$SkipPrepare,
    [switch]$SkipCapture
)
throw 'Pipeline historique archive : ouvrir Capitale. Ne pas regenerer les anciennes cartes d essai.'
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$python=Join-Path $root '.venv/Scripts/python.exe'
$editor=Join-Path $EnginePath 'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$project=Join-Path $root 'JustAnotherRpgGame.uproject'
$report=Join-Path $root 'Saved/Jadg/capital-landscape-districts'
$script=(Join-Path $root 'scripts/maps/build_capital_landscape_districts.py') -replace '\\','/'
$cache=(Join-Path $root 'Saved/DerivedDataCache') -replace '\\','/'
$cacheArgs=@("-ZenDataPath=$cache/Zen","-LocalDataCachePath=$cache",'-noxgeshadercompile','-nowrite')
if($ZenPort -gt 0){$cacheArgs += "-NoZenAutoLaunch=localhost:$ZenPort"}
if(Get-Process -Name UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue){throw 'Une instance Unreal utilise le projet.'}
New-Item -ItemType Directory -Force -Path $report | Out-Null
$previousTemp=$env:TEMP
$previousTmp=$env:TMP
$env:TEMP=Join-Path $report 'Temp'
$env:TMP=$env:TEMP
New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null
function Invoke-District([string]$Key,[string]$Stage){
    $folder=Join-Path $report $Key
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
    $started=Get-Date
    & $editor $project -run=pythonscript "-script=$script" "-CapitalDistrict=$Key" "-CapitalPhase=$Stage" @cacheArgs -AllowCommandletRendering -RenderOffscreen -unattended -nosplash -NoSound -stdout -FullStdOutLogOutput *> (Join-Path $folder "$Stage.log")
    if($LASTEXITCODE -ne 0){throw "Quartier $Key, phase $Stage echouee."}
    $proof=if($Stage -eq 'assemble'){Join-Path $report 'assembly.json'}else{Join-Path $folder '05-review-map.json'}
    if(-not(Test-Path -LiteralPath $proof) -or (Get-Item -LiteralPath $proof).LastWriteTime -lt $started){throw "Unreal n'a pas produit de rapport frais : $Key/$Stage"}
    if(Select-String -LiteralPath (Join-Path $folder "$Stage.log") -Pattern 'LogPython: Error:|Fatal error|Failed to compile Material' -Quiet){throw "Erreur Unreal : $Key/$Stage"}
    Write-Output "Quartier $Key : $Stage termine."
}
Push-Location $root
try{
    if($Phase -eq 'All' -and -not $SkipPrepare){
        & $python scripts/maps/prepare_capital_landscape_districts.py
        if($LASTEXITCODE -ne 0){throw 'Preparation du terrain echouee.'}
        & $BlenderPath --background --python scripts/assetsGeneration/build_capital_landscape_water.py *> (Join-Path $report 'water.log')
        if($LASTEXITCODE -ne 0){throw 'Preparation des eaux echouee.'}
    }
    $manifest=Get-Content -Raw -LiteralPath (Join-Path $report 'manifest.json') | ConvertFrom-Json
    $selected=@($manifest.districts | Where-Object {$Districts.Count -eq 0 -or $_.id -in $Districts})
    foreach($q in $selected){
        if($Phase -in @('All','Build')){
            $audit=Join-Path $report "$($q.id)/04-audit.json"
            $done=$false
            if($Resume -and (Test-Path -LiteralPath $audit)){
                $savedAudit=Get-Content -Raw -LiteralPath $audit | ConvertFrom-Json
                $done=$savedAudit.errors.Count -eq 0 -and (Test-Path -LiteralPath (Join-Path $report "$($q.id)/05-review-map.json"))
            }
            if(-not $done){Invoke-District $q.id $BuildStage}
            else {Write-Output "Quartier $($q.id) deja construit; audit conserve."}
        }
        if($Phase -eq 'Capture' -or ($Phase -eq 'All' -and -not $SkipCapture)){
            $output=Join-Path $root "Saved/Captures/capital-landscape-districts/$($q.slug)"
            New-Item -ItemType Directory -Force -Path $output | Out-Null
            $start=Get-Date
            & $editor $project "/Game/Maps/Levels/capital-landscape/paysage-$($q.slug)" @cacheArgs -game -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound "-JadgCapture=$output" '-JadgHours=12:00,22:00' -JadgSettle=180 -JadgMeasure=3 -stdout -FullStdOutLogOutput *> (Join-Path $report "$($q.id)/capture.log")
            if($LASTEXITCODE -ne 0){throw "Capture de $($q.name) echouee."}
            if(Select-String -LiteralPath (Join-Path $report "$($q.id)/capture.log") -Pattern 'Failed to compile Material|Fatal error' -Quiet){throw "Erreur de rendu : $($q.id)"}
            foreach($n in 1,2){foreach($hour in '1200','2200'){
                $file=Join-Path $output "$($q.slug)-$n-$hour.png"
                if(-not(Test-Path -LiteralPath $file) -or (Get-Item -LiteralPath $file).LastWriteTime -lt $start){throw "Capture absente : $file"}
            }}
            Write-Output "Quartier $($q.id) : quatre captures produites."
        }
    }
    if($Phase -eq 'Assemble' -or ($Phase -eq 'All' -and $Districts.Count -eq 0)){
        foreach($q in $manifest.districts){
            $audit=Get-Content -Raw -LiteralPath (Join-Path $report "$($q.id)/04-audit.json") | ConvertFrom-Json
            if($audit.errors.Count -gt 0){throw "Audit non valide : $($q.id)"}
        }
        Invoke-District 'Q07' 'assemble'
    }
} finally {
    Pop-Location
    $env:TEMP=$previousTemp
    $env:TMP=$previousTmp
}
