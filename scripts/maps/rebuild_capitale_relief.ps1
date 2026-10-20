<#
.SYNOPSIS
Reconstruit le relief naturel de la capitale (/Game/Capitale/Cartes/Capitale) depuis sa description texte.

.DESCRIPTION
Enchaîne, sans fenêtre, ce qui produit la carte active depuis le dépôt :

  relief     prepare_capitale_reference.py : le Guide de Creation (PDF) lu planche par planche :
             relief des courbes (06), rivage, voies (04) pavees dans l'enceinte (01), couvert (02)
  eau        prepare_capitale_reference_water.py : surfaces d'eau par tuile
  matiere    build_capitale_terrain_material.py : M_TerrainNaturel, MI_TerrainNaturel, RVT
  monde      build_reference_relief.py : Capitale_Reconstruction (16 Landscape a deux couches d'edition, eau, ciel)
  partition  WorldPartitionConvertCommandlet sur Capitale_Reconstruction
  retrait    retire_previous_capitale.py : l'ancienne carte, seulement si -Sauvegarde la contient à l'identique
  renommage  WorldPartitionRenameDuplicateBuilder : Capitale_Reconstruction devient Capitale
  nanite     finalize_reference_relief.py : Nanite construit tuile par tuile (poste de 16 Go), hauteurs vérifiées
  streaming  configure_capitale_streaming.py : streaming World Partition, cellules et portées, HLOD
  sans-vegetation retire_capitale_vegetation.py : aucune vegetation sur la carte (demande de l'auteur
             du 19 octobre 2026), ni foret PCG ni herbe ; sans effet sur une carte deja nue
  arene      place_capitale_arena.py : l'Arena of Fate du LOT-1022 posee a son emprise (manifest.json, cle arena)
  demo       capitale_demo.py : la demo autour de l'arene (quete des pommes) : carte de Core
             Source/Elements/Levels/Capitale.json, groupe, personnages, navigation, repere
  navigation WorldPartitionNavigationDataBuilder : le maillage de navigation de l'arene, construit au
             profil fin avec la carte (Static), en morceaux charges avec les cellules
  hlod       WorldPartitionHLODsBuilder : les HLOD du relief et de l'eau, vus de loin
  controle   verify_reference_capitale.py, verify_capitale_arena_access.py (gradins de l'arene
             et personnages de la demo atteints depuis le parvis), puis configure_capitale_workspace.py (cadrages)
  captures   chaque cadrage de views.json, à 12:00 et à 22:00

.PARAMETER Etapes
Les étapes à jouer, dans l'ordre ci-dessus (toutes par défaut).

.PARAMETER Sauvegarde
Dossier qui contient la copie vérifiée de l'ancienne carte (Content/...), exigé par l'étape « retrait ».

.EXAMPLE
pwsh scripts/maps/rebuild_capitale_relief.ps1 -Sauvegarde Saved/Sauvegardes/capitale-avant-rivage-v04-20261017
#>
param(
    [string[]]$Etapes = @('relief', 'eau', 'matiere', 'monde', 'partition', 'retrait', 'renommage', 'nanite', 'streaming', 'sans-vegetation', 'arene', 'demo', 'navigation', 'hlod', 'controle', 'captures'),
    [string]$Sauvegarde,
    [string]$EnginePath = 'E:\Epic Games\UE_5.8',
    [string]$Captures
)
$ErrorActionPreference = 'Stop'
# « -Etapes a,b » arrive en une seule chaîne quand le script est lancé par -File.
$Etapes = $Etapes -split ',' | Where-Object { $_ }
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$uproject = Join-Path $root 'JustAnotherRpgGame.uproject'
$editor = Join-Path $EnginePath 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$python = Join-Path $root '.venv\Scripts\python.exe'
$logs = Join-Path $root 'Saved\Jadg\capitale-relief'
New-Item -ItemType Directory -Force $logs | Out-Null
if (-not $Captures) { $Captures = Join-Path $logs 'captures' }
$cache = @("-ZenDataPath=$root/Saved/DerivedDataCache/Zen", "-LocalDataCachePath=$root/Saved/DerivedDataCache", '-noxgeshadercompile')
$quiet = @('-unattended', '-nosplash', '-NoSound', '-stdout', '-FullStdOutLogOutput')
# Les Landscape et Nanite se construisent avec le rendu : pas de -nullrhi.
$render = @('-AllowCommandletRendering', '-ini:Engine:[SystemSettings]:Editor.AsyncStaticMeshCompilation=0')

function Step([string]$Name, [scriptblock]$Body) {
    if ($Etapes -notcontains $Name) { return }
    Write-Host "== $Name ==" -ForegroundColor Cyan
    & $Body
}

function Editor([string]$Name, [string[]]$Arguments, [string]$Marker, [switch]$SansRendu) {
    $log = Join-Path $logs "$Name.log"
    $mode = if ($SansRendu) { @('-nullrhi', '-ini:Engine:[SystemSettings]:Editor.AsyncStaticMeshCompilation=0') } else { $render }
    $line = (@("`"$uproject`"") + $Arguments + $mode + $cache + $quiet | ForEach-Object {
            if ($_ -match ' ' -and $_ -notmatch '^"') { "`"$_`"" } else { $_ } }) -join ' '
    $run = Start-Process $editor -ArgumentList $line -PassThru -NoNewWindow -RedirectStandardOutput $log
    # Sur ce poste, l'éditeur sans fenêtre reste parfois bloqué à la fermeture, son travail fini :
    # passé 90 s après la fin du commandlet, il est arrêté et le journal fait foi.
    $finished = $null
    while (-not $run.HasExited) {
        Start-Sleep -Seconds 5
        if (-not $finished -and (Select-String -Path $log -Pattern 'Execution of commandlet took' -Quiet)) { $finished = Get-Date }
        if ($finished -and ((Get-Date) - $finished).TotalSeconds -gt 90) {
            Write-Host "  ($Name : éditeur bloqué à la fermeture, arrêté)" -ForegroundColor DarkGray
            Stop-Process -Id $run.Id -Force
            break
        }
    }
    if (-not (Select-String -Path $log -Pattern 'Success - 0 error' -Quiet)) { throw "$Name : le commandlet signale des erreurs (journal : $log)" }
    if ($Marker -and -not (Select-String -Path $log -Pattern $Marker -Quiet)) {
        throw "$Name : le marqueur $Marker manque (journal : $log)"
    }
    $failed = Select-String -Path $log -Pattern 'Failed to compile Material|Traceback \(most recent' | Select-Object -First 3
    if ($failed) { throw "$Name : $($failed[0].Line) (journal : $log)" }
}

function Python([string]$Script) {
    & $python (Join-Path $root "scripts\maps\$Script")
    if ($LASTEXITCODE -ne 0) { throw "$Script : code $LASTEXITCODE" }
}

function Script([string]$Name) { "-script=$root/scripts/maps/$Name" }

Step 'relief' { Python 'prepare_capitale_reference.py' }
Step 'eau' { Python 'prepare_capitale_reference_water.py' }
Step 'matiere' { Editor 'matiere' @('-run=pythonscript', (Script 'build_capitale_terrain_material.py')) 'CAPITALE_TERRAIN_MATERIAL_READY' }
Step 'monde' { Editor 'monde' @('-run=pythonscript', (Script 'build_reference_relief.py')) 'REFERENCE_WORLD_READY' }
Step 'partition' {
    # Réglages de la conversion (grille des Landscape, hachage), lus à côté de la carte convertie.
    Copy-Item (Join-Path $root 'Source\Elements\Terrain\capital\relief-reference\world-partition-conversion.ini') `
        (Join-Path $root 'Content\Capitale\Cartes\Capitale_Reconstruction.ini') -Force
    Editor 'partition' @('-run=WorldPartitionConvertCommandlet', '/Game/Capitale/Cartes/Capitale_Reconstruction', '-SkipStableGUIDValidation') $null
}
Step 'retrait' {
    if (-not $Sauvegarde) { throw 'retrait : -Sauvegarde est exigé (copie vérifiée de la carte remplacée).' }
    $backup = (Resolve-Path $Sauvegarde).Path -replace '\\', '/'
    Editor 'retrait' @('-run=pythonscript', (Script 'retire_previous_capitale.py'), "-JadgBackup=$backup") 'PREVIOUS_CAPITALE_RETIRED_BACKUP_VERIFIED'
}
Step 'renommage' {
    # Un éditeur arrêté à sa fermeture n'a pas réécrit le cache du registre d'assets : le renommeur y
    # trouverait les acteurs de la carte retirée. Le cache est mis de côté (il se reconstruit).
    $aside = Join-Path $logs ('cache-registre-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    New-Item -ItemType Directory -Force $aside | Out-Null
    Get-ChildItem (Join-Path $root 'Intermediate') -Filter 'CachedAssetRegistry*' -ErrorAction SilentlyContinue | Move-Item -Destination $aside
    # Les dossiers d'acteurs externes de la carte retirée suffisent aussi à l'égarer.
    foreach ($kind in '__ExternalActors__', '__ExternalObjects__') {
        $folder = Join-Path $root "Content\$kind\Capitale\Cartes\Capitale"
        # Carte retirée (sa sauvegarde vérifiée) : ses dossiers externes sont orphelins, quoi qu'ils contiennent.
        $orphan = -not (Test-Path (Join-Path $root 'Content\Capitale\Cartes\Capitale.umap'))
        if ((Test-Path $folder) -and ($orphan -or -not (Get-ChildItem $folder -Recurse -File))) { Move-Item $folder (Join-Path $aside $kind) }
    }
    try {
        Editor 'renommage' @('/Game/Capitale/Cartes/Capitale_Reconstruction', '-run=WorldPartitionBuilderCommandlet',
            '-builder=WorldPartitionRenameDuplicateBuilder', '-NewPackage=/Game/Capitale/Cartes/Capitale', '-Rename') $null
    } catch {
        # Le constructeur échoue souvent à effacer la source après avoir écrit la copie : la copie
        # suffit, la source est retirée par l'étape suivante.
        $log = Join-Path $logs 'renommage.log'
        if (-not (Select-String -Path $log -Pattern 'Saving new map packages took' -Quiet) -or
            -not (Select-String -Path $log -Pattern 'Failed to delete source packages' -Quiet)) { throw }
        Write-Host '  (renommage : copie écrite, source laissée à retirer)' -ForegroundColor DarkGray
    }
}
# Sans rendu : charger avec rendu des Landscape Nanite encore sans maillage plante l'éditeur
# (assertion IsInGameThread dans ShowFlags.cpp, 17 octobre 2026). Le maillage Nanite se construit au processeur.
Step 'nanite' { Editor 'nanite' @('-run=pythonscript', (Script 'finalize_reference_relief.py')) 'REFERENCE_AUDIT_READY' -SansRendu }
Step 'streaming' { Editor 'streaming' @('-run=pythonscript', (Script 'configure_capitale_streaming.py')) 'CAPITALE_STREAMING_READY' -SansRendu }
Step 'sans-vegetation' { Editor 'sans-vegetation' @('-run=pythonscript', (Script 'retire_capitale_vegetation.py')) 'CAPITALE_SANS_VEGETATION' -SansRendu }
Step 'arene' { Editor 'arene' @('-run=pythonscript', (Script 'place_capitale_arena.py')) 'CAPITALE_ARENA_READY' }
Step 'demo' { Editor 'demo' @('-run=pythonscript', (Script 'capitale_demo.py')) 'CAPITALE_DEMO_READY' -SansRendu }
Step 'navigation' {
    Editor 'navigation' @('/Game/Capitale/Cartes/Capitale', '-run=WorldPartitionBuilderCommandlet', '-Builder=WorldPartitionNavigationDataBuilder') $null -SansRendu
}
# Les HLOD du Landscape cuisent sa matière : avec le rendu (Nanite déjà construit à l'étape précédente).
Step 'hlod' {
    Editor 'hlod' @('/Game/Capitale/Cartes/Capitale', '-run=WorldPartitionBuilderCommandlet', '-Builder=WorldPartitionHLODsBuilder') $null
}
Step 'controle' {
    # Le monde de reconstruction que le renommeur laisse sur le disque n'a plus tous ses acteurs : il
    # est mis de côté (build_reference_relief.py le refait). Ses couches HLOD restent, Capitale les cite.
    $aside = Join-Path $logs ('reconstruction-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    $maps = Join-Path $root 'Content\Capitale\Cartes\Capitale_Reconstruction.umap'
    if (Test-Path $maps) {
        New-Item -ItemType Directory -Force $aside | Out-Null
        Move-Item $maps $aside
        foreach ($kind in '__ExternalActors__', '__ExternalObjects__') {
            $folder = Join-Path $root "Content\$kind\Capitale\Cartes\Capitale_Reconstruction"
            if (Test-Path $folder) { Move-Item $folder (Join-Path $aside $kind) }
        }
    }
    Editor 'verification' @('-run=pythonscript', (Script 'verify_reference_capitale.py')) 'CAPITALE_REFERENCE_FINAL_OK'
    Editor 'acces' @('-run=pythonscript', (Script 'verify_capitale_arena_access.py')) 'CAPITALE_ARENA_ACCESS' -SansRendu
    Editor 'cadrages' @('-run=pythonscript', (Script 'configure_capitale_workspace.py')) 'CLEAN_CAPITAL_VIEWS_READY'
}
Step 'captures' {
    $shots = (Get-Content (Join-Path $root 'Source\Elements\Terrain\capital\relief-reference\views.json') -Raw | ConvertFrom-Json).id -join ','
    New-Item -ItemType Directory -Force $Captures | Out-Null
    $log = Join-Path $logs 'captures.log'
    # Une ligne de commande d'un seul tenant : -ExecCmds garde ses guillemets et ses espaces.
    $arguments = "`"$uproject`" /Game/Capitale/Cartes/Capitale -game -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes " +
        "-unattended -nosplash -NoSound -ExecCmds=`"r.Streaming.PoolSize 4000,r.Streaming.FullyLoadUsedTextures 1`" " +
        "-JadgCapture=`"$Captures`" -JadgShots=$shots -JadgHours=12:00,22:00 -JadgMeasure=2 -JadgSettle=180 " +
        "$($cache -join ' ') -stdout -FullStdOutLogOutput"
    $run = Start-Process (Join-Path $EnginePath 'Engine\Binaries\Win64\UnrealEditor.exe') -ArgumentList $arguments `
        -Wait -PassThru -NoNewWindow -RedirectStandardOutput $log
    if ($run.ExitCode -ne 0) { throw "captures : code $($run.ExitCode) (journal : $log)" }
    Get-ChildItem $Captures -Filter *.png | ForEach-Object { Write-Host "  $($_.Name)" }
}
Write-Host 'Relief de la capitale reconstruit.' -ForegroundColor Green
