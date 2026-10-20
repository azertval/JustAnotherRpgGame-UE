<# World Partition delivery from completed landscape district workshops.
Generated conversion intermediates:
/Game/Maps/Levels/capital-landscape/construction-capitale_OFPA
/Game/Maps/Levels/capital-landscape/construction-capitale_OFPA_WP
/Game/Maps/Levels/capital-landscape/construction-capitale_OFPA_HLODLayer_Instanced
/Game/Maps/Levels/capital-landscape/construction-capitale_OFPA_HLODLayer_Merged
Generated final world and external actor packages:
/Game/Capitale/Cartes/Capitale
/Game/__ExternalActors__/Maps/Levels/capital-landscape
/Game/__ExternalObjects__/Maps/Levels/capital-landscape
#>
[CmdletBinding()]
param(
    [ValidateSet('All','Convert','Partition','Finalize','Configure','HLOD','Audit','Capture','Streaming','Minimap')][string]$Phase='All',
    [string]$EnginePath='E:\Epic Games\UE_5.8',
    [int]$ZenPort=0
)
throw 'Pipeline historique archive : ouvrir Capitale. Ne pas regenerer les anciennes cartes d essai.'
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$editor=Join-Path $EnginePath 'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$project=Join-Path $root 'JustAnotherRpgGame.uproject'
$report=Join-Path $root 'Saved/Jadg/capital-landscape-districts/world-partition'
$cache=(Join-Path $root 'Saved/DerivedDataCache') -replace '\\','/'
$base='/Game/Maps/Levels/capital-landscape/'
$final=$base+'paysage-capitale'
$flags=@("-ZenDataPath=$cache/Zen","-LocalDataCachePath=$cache",'-noxgeshadercompile','-nowrite','-unattended','-nosplash','-NoSound','-stdout','-FullStdOutLogOutput','-SCCProvider=None')
if($ZenPort -gt 0){$flags+="-NoZenAutoLaunch=localhost:$ZenPort"}
if(Get-Process -Name UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue){throw 'Une instance Unreal utilise le projet.'}
New-Item -ItemType Directory -Force -Path $report | Out-Null
$previousTemp=$env:TEMP
$previousTmp=$env:TMP
$env:TEMP=Join-Path $report 'Temp'
$env:TMP=$env:TEMP
New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null
function Invoke-Unreal([string]$Name,[string[]]$Arguments){
    $log=Join-Path $report "$Name.log"
    & $editor $project @Arguments @flags *> $log
    if($LASTEXITCODE -ne 0 -or (Get-Item -LiteralPath $log).Length -eq 0){throw "World Partition : $Name a echoue."}
    if(Select-String -LiteralPath $log -Pattern 'LogPython: Error:|Fatal error|Failed to compile Material' -Quiet){throw "World Partition : erreur dans $Name."}
    Write-Output "World Partition : $Name termine."
}
Push-Location $root
try{
    if($Phase -in @('All','Convert')){
        # UE-353028: first merge landscapes into the persistent level, then partition.
        # Both conversions use suffixes, preserving the individual district workshops.
        Invoke-Unreal '01-merge' @('-run=WorldPartitionConvertCommandlet',($base+'construction-capitale'),'-OnlyMergeSubLevels','-ConversionSuffix','-AllowCommandletRendering','-nullrhi')
    }
    if($Phase -in @('All','Convert','Partition')){
        Copy-Item -LiteralPath 'Source/Elements/Terrain/capital/world-partition.ini' -Destination 'Content/Maps/Levels/capital-landscape/construction-capitale_OFPA.ini' -Force
        Invoke-Unreal '02-convert' @('-run=JadgConvertCapital',($base+'construction-capitale_OFPA'),'-ConversionSuffix','-AllowCommandletRendering','-RenderOffscreen')
    }
    if($Phase -in @('All','Convert','Partition','Finalize')){
        Invoke-Unreal '03-final-map' @(($base+'construction-capitale_OFPA_WP'),'-run=WorldPartitionBuilderCommandlet','-Builder=WorldPartitionRenameDuplicateBuilder',"-NewPackage=$final",'-nullrhi')
        $generatedIni=Join-Path $root 'Content/Maps/Levels/capital-landscape/construction-capitale_OFPA.ini'
        if(Test-Path -LiteralPath $generatedIni){Remove-Item -LiteralPath $generatedIni}
    }
    $configure=(Join-Path $root 'scripts/maps/configure_capital_world_partition.py') -replace '\\','/'
    if($Phase -in @('All','Configure')){
        Invoke-Unreal '04-configure' @('-run=pythonscript',"-script=$configure",'-CapitalWP=configure','-AllowCommandletRendering','-RenderOffscreen')
    }
    if($Phase -in @('All','HLOD')){
        Invoke-Unreal '05-hlod' @($final,'-run=WorldPartitionBuilderCommandlet','-Builder=WorldPartitionHLODsBuilder','-AllowCommandletRendering','-RenderOffscreen')
    }
    if($Phase -in @('All','Audit')){
        Invoke-Unreal '06-audit' @('-run=pythonscript',"-script=$configure",'-CapitalWP=audit','-nullrhi')
        $audit=Get-Content -Raw -LiteralPath (Join-Path $report 'audit.json') | ConvertFrom-Json
        if(-not $audit.streaming -or $audit.errors.Count -gt 0){throw 'Audit World Partition invalide.'}
    }
    if($Phase -in @('All','Capture')){
        $output=Join-Path $root 'Saved/Captures/capital-world-partition'
        New-Item -ItemType Directory -Force -Path $output | Out-Null
        Invoke-Unreal '07-capture' @($final,'-game','-RenderOffscreen','-ResX=1920','-ResY=1080','-ForceRes',"-JadgCapture=$output",'-JadgHours=12:00,22:00','-JadgSettle=180','-JadgMeasure=3')
    }
    if($Phase -in @('All','Streaming')){
        $route=Join-Path $report 'streaming-route.json'
        if(-not(Test-Path -LiteralPath $route)){throw 'Parcours de streaming absent.'}
        Invoke-Unreal '08-streaming' @($final,'-game','-JadgSansTitre','-RenderOffscreen','-ResX=1920','-ResY=1080','-ForceRes',"-JadgLandscapeStreaming=$route")
        $measure=Get-Content -Raw -LiteralPath (Join-Path $report 'streaming-performance.json') | ConvertFrom-Json
        if($measure.error -or -not $measure.worldPartition){throw 'Parcours World Partition invalide.'}
        $expected=Get-Content -Raw -LiteralPath $route | ConvertFrom-Json
        $stops=@($measure.measurements | Where-Object {-not $_.continuous})
        $travel=@($measure.measurements | Where-Object continuous)
        if($stops.Count -ne $expected.stops.Count -or $travel.Count -ne 1){throw 'Parcours World Partition incomplet.'}
        if($travel[0].groundProbes -lt 200 -or $travel[0].missingGroundProbes -ne 0){throw 'Continuite du terrain non validee.'}
        if(@($measure.measurements | Where-Object {$_.loadedLandscapeProxies -ge 572}).Count){throw 'Le monde entier reste charge.'}
    }
    if($Phase -in @('All','Minimap')){
        Invoke-Unreal '09a-minimap-settings' @('-run=pythonscript',"-script=$configure",'-CapitalWP=minimap','-nullrhi')
        Invoke-Unreal '09b-minimap' @($final,'-run=WorldPartitionBuilderCommandlet','-Builder=WorldPartitionMiniMapBuilder','-AllowCommandletRendering','-RenderOffscreen')
        Invoke-Unreal '09c-minimap-audit' @('-run=pythonscript',"-script=$configure",'-CapitalWP=minimap_audit','-nullrhi')
    }
} finally {
    Pop-Location
    $env:TEMP=$previousTemp
    $env:TMP=$previousTmp
}
