<#
.SYNOPSIS
    Construit et vérifie JustAnotherRpgGame sans ouvrir une fenêtre (LOT-1014).

.DESCRIPTION
    Deux constructions, une règle : sortir en 1 à la première erreur.

    - Par défaut, les tests de Core HORS du moteur : CMake + Ninja + GoogleTest sur
      Source/JustAnotherRpgGame/Core, dans un environnement MSVC x64 que le script établit lui-même
      (vswhere, puis vcvars64.bat : une « Developer PowerShell » démarre en x86).
    - Avec -Unreal, le projet du moteur, en cinq temps :
        1. UnrealBuildTool construit la cible d'éditeur ;
        2. le commandlet JadgContentCheck lit les données de contenu par les lecteurs de Core et
           compte ses erreurs ;
        3. les tests d'automatisation du moteur (Jadg.*) tournent sans processeur graphique, et
           leur rapport est relu : aucun échec, aucun test non lancé, au moins un test passé ;
        4. les cartes sont contrôlées (scripts/maps/jadg_map.py --check), puis l'aller-retour
           entre le texte et l'éditeur est rejoué sur la carte à deux étages
           (scripts/maps/check_level_roundtrip.py, LOT-1018) ;
        5. le niveau d'une carte est construit par script depuis sa description v5
           (scripts/maps/build_level.py), son maillage de navigation contrôlé ;
        6. le jeu est lancé hors écran sur ce niveau, ses captures sont prises, puis comparées
           à tolérance à leur référence si la carte en a une (Source/Test/Fixtures/Captures/).
      Sans -Map, la carte est celle du socle (socle-1014) : elle ne lit aucun kit d'assets, ses
      captures ont une référence, et les temps 5 et 6 se font d'office. -NoCapture les saute, sur
      un poste sans processeur graphique.
      Le moteur est trouvé par l'association du .uproject (registre HKCU\Software\Epic Games\
      Unreal Engine\Builds), ou par -EnginePath ; sa version doit être celle que ci.yml épingle
      (UNREAL_ENGINE_VERSION).

.PARAMETER Unreal
    Construire le projet Unreal, contrôler le contenu, lancer les tests d'automatisation, puis
    construire la scène du socle et comparer ses captures à leur référence.

.PARAMETER Map
    Avec -Unreal : construire le niveau de cette carte, par son identifiant (porte-1012,
    essai/etages, central-empire/capital/martpart…), depuis sa description v5 par
    scripts/maps/build_level.py, sans fenêtre (LOT-1018), à la place de celle du socle. Ses
    captures ne se prennent qu'avec -Capture. -Scene en est l'ancien nom.

.PARAMETER Capture
    Avec -Map : lancer ensuite le jeu hors écran sur cette carte, prendre les captures aux
    cadrages et aux heures de la description, mesurer la cadence, et vérifier que chaque image est
    écrite. Sorties dans Saved/Captures/<carte>/ (« / » devient « - »). Demande un processeur
    graphique.

.PARAMETER NoCapture
    Avec -Unreal, sans -Map : ne pas construire la carte du socle ni prendre ses captures.

.PARAMETER Parcours
    Avec -Unreal, à la place de -Map : construire les cartes d'essai de l'exploration
    (essai/etals, essai/parvis, LOT-1016) et l'arène du combat (essai/arene, LOT-1017), puis
    lancer le jeu hors écran sur la première et y jouer la quête « Des pommes pour
    l'arène » sans personne, par les touches et les clics du joueur, injectés dans son contrôleur :
    l'essai de chaque commande de caméra, la mère, le coffre, le portail, le garde (jet de
    Persuasion, graine -Seed), le maître d'arène (« attendre » : le combat a son parcours), le
    retour. Chaque réplique est capturée, HUD compris. Sorties dans Saved/Captures/parcours-1016/.
    Demande un processeur graphique.

.PARAMETER ParcoursCombat
    Avec -Unreal, à la place de -Map : construire le parvis d'essai et l'Arena of Fate, puis lancer
    le jeu hors écran sur le parvis et y jouer, par les touches et les clics du joueur, le début de
    la série de l'arène (LOT-1017) : le maître d'arène, « combattre », la rencontre arene-bandits
    sur le sable de l'Arena of Fate (la carte d'arène du jeu, LOT-1022) jusqu'à son issue — chaque
    tour d'un héros traduit en clics et en touches, ceux des bandits joués par l'IA —, le retour au
    parvis. Code 0 sur la victoire du groupe revenu là où il était. Graine du combat : -Seed.
    Sorties dans Saved/Captures/parcours-1017/.

.PARAMETER ParcoursDemo
    Avec -Unreal, à la place de -Map : construire Martpart, Arenarea et l'Arena of Fate, puis lancer
    le jeu hors écran sur Martpart et y marcher la démo de carte en carte par les ordres du joueur
    (LOT-1022) : Martpart, Arenarea, l'Arena of Fate — le vestibule des vestiaires, le sable, les
    catacombes —, Arenarea, retour à Martpart. Code 0 de retour à Martpart. Sorties dans
    Saved/Captures/parcours-demo-1022/.

.PARAMETER Ecrans
    Avec -Unreal, à la place de -Map : construire la carte d'essai des étals et l'arène d'essai,
    puis lancer le jeu hors écran et y faire le tour des écrans (LOT-1020) : chaque écran ouvert
    par sa touche, parcouru au clavier et à la souris par des touches et des clics injectés,
    capturé interface comprise, refermé ; le jeu passé en anglais par l'écran Options ; puis
    l'interface du combat sur l'arène d'essai (-JadgArene, LOT-1022), la rencontre arene-bandits
    montée et figée au tour du joueur. Captures comparées à tolérance à Source/Test/Fixtures/Captures/ecrans-1020/
    (-UpdateReference pour la réécrire). Sorties dans Saved/Captures/ecrans-1020/. Demande un
    processeur graphique.

.PARAMETER Seed
    Avec -Parcours : la graine du jet de Persuasion (défaut : 1, qui le réussit — relevé par le
    test Jadg.Exploration.QueteDesPommes). Avec -ParcoursCombat : la graine du combat.

.PARAMETER Encounter
    Avec -Map et -Capture, sur une carte d'arène : la rencontre engagée au lancement, montée et
    figée sur son déploiement pendant les captures et la mesure (LOT-1017) ; la carte est l'arène
    du passage (-JadgArene).

.PARAMETER Etages
    Avec -Map et -Capture, sur une carte découpée en niveaux de chargement par étage (LOT-1022) :
    les seuls étages montrés pendant le passage, par leur rang (« 1 », « 0,1,2 ») ; seuls les
    cadrages qui les regardent sont pris, et la cadence est celle de ces étages. Sorties dans
    Saved/Captures/<carte>-etages-<rangs>/.

.PARAMETER UpdateReference
    Avec des captures : réécrire leur référence (les images de blocs de
    Source/Test/Fixtures/Captures/<carte>/) au lieu de les y comparer. Pour une image qui a changé
    exprès ; les vignettes se relisent dans la PR.

.PARAMETER MeasureSeconds
    Durée de la mesure de cadence, par heure (défaut : 10 s, caméra en mouvement).

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
    Construit l'éditeur du projet, vérifie le contenu, lance les tests du moteur, contrôle les
    cartes et rejoue leur aller-retour, reconstruit la carte du socle et compare ses captures à
    leur référence, sans fenêtre.

.EXAMPLE
    pwsh scripts/build.ps1 -Unreal -Map porte-1012 -Capture
    Construit, vérifie, reconstruit le niveau de la porte, puis en prend les captures et la mesure.

.EXAMPLE
    pwsh scripts/build.ps1 -Unreal -Map controle/arenarea-palazzo-terracotta -Capture
    Construit la carte de contrôle d'une pièce de décor (scripts/maps/build_piece_check.py,
    LOT-1019) et en prend les quatre côtés, à midi et à 22 h.

.EXAMPLE
    pwsh scripts/build.ps1 -Unreal -Ecrans
    Construit, vérifie, puis fait le tour des écrans dans le jeu lancé hors écran et compare leurs
    captures à leur référence.

.EXAMPLE
    pwsh scripts/build.ps1 -Unreal -Map central-empire/capital/arenarea/arena-of-fate -Capture -Etages 1
    Construit l'Arena of Fate, puis en prend les cadrages des vestiaires et la cadence, les seuls
    vestiaires montrés (LOT-1022).

.EXAMPLE
    pwsh scripts/build.ps1 -Unreal -ParcoursDemo
    Construit les trois lieux de la démo, puis la marche de Martpart à l'Arena of Fate et retour.

.EXAMPLE
    pwsh scripts/build.ps1 -Unreal -Parcours
    Construit, vérifie, reconstruit les cartes d'essai de l'exploration, puis y joue la quête des
    pommes dans le jeu lancé hors écran.
#>
[CmdletBinding()]
param(
    [switch]$Unreal,
    [Alias('Scene')]
    [string]$Map,
    [switch]$Capture,
    [switch]$NoCapture,
    [switch]$Parcours,
    [switch]$ParcoursCombat,
    [switch]$ParcoursDemo,
    [switch]$Ecrans,
    [int]$Seed = 1,
    [string]$Encounter,
    [string]$Etages,
    [switch]$UpdateReference,
    [int]$MeasureSeconds = 10,
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

# La carte que -Unreal construit et capture d'office : elle ne lit aucun kit d'assets (LOT-1014).
$SocleMap = 'socle-1014'

function Get-Python {
    # L'environnement du dépôt (uv sync) s'il existe : ses versions sont celles de uv.lock.
    $venv = Join-Path $root '.venv\Scripts\python.exe'
    if (Test-Path $venv) { return $venv }
    return 'python'
}

function Get-MapInfo([string]$mapId) {
    # Ce que la description d'une carte dit au build : son fichier, son niveau, ses cadrages, ses heures.
    $info = & (Get-Python) (Join-Path $root 'scripts\maps\jadg_map.py') --info $mapId
    if ($LASTEXITCODE -ne 0) { Fail "Carte « $mapId » introuvable (scripts/maps/jadg_map.py --info)." }
    return ($info | Out-String | ConvertFrom-Json)
}

function Invoke-LevelBuild([string]$editorCmd, [string]$mapId) {
    # Le niveau d'une carte, construit par script depuis sa description (LOT-1018), son maillage de
    # navigation contrôlé. Chemin absolu : le moteur résout un chemin relatif depuis ses binaires.
    $builder = (Join-Path $root 'scripts\maps\build_level.py') -replace '\\', '/'
    Write-Host "== Carte « $mapId » : construction du niveau par script (sans fenêtre) ==" -ForegroundColor Cyan
    & $editorCmd "$uproject" -run=pythonscript "-script=$builder" "-JadgMap=$mapId" -JadgCheck -unattended -nosplash -nullrhi -NoSound -stdout -FullStdOutLogOutput
    if ($LASTEXITCODE -ne 0) { Fail "La construction du niveau de $mapId a échoué (code $LASTEXITCODE)." }
}

function Assert-Completed([string]$journal, [string]$what) {
    # Le moteur lancé en jeu depuis l'éditeur ne rend pas toujours le code de sortie que le parcours
    # demande (LOT-1022 : un parcours arrêté sortait en 0) ; le journal dit s'il est allé au bout.
    $done = (Get-Content $journal -Raw -Encoding UTF8 | ConvertFrom-Json).completed
    if (-not $done) { Fail "$what ne s'est pas terminé : $journal" }
}

function Get-PinnedEngineVersion {
    # Une version par outil, écrite dans le bloc env: de ci.yml et nulle part ailleurs.
    $ci = Get-Content (Join-Path $root '.github\workflows\ci.yml') -Encoding UTF8
    foreach ($line in $ci) {
        if ($line -match '^\s+UNREAL_ENGINE_VERSION:\D*([0-9.]+)') { return $Matches[1] }
    }
    Fail 'UNREAL_ENGINE_VERSION introuvable dans .github/workflows/ci.yml.'
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

    # Le moteur trouvé est celui que le dépôt épingle : une autre version construit peut-être,
    # mais ne rend ni n'importe pareil.
    $pinned = Get-PinnedEngineVersion
    $installed = Get-Content (Join-Path $EnginePath 'Engine\Build\Build.version') -Raw | ConvertFrom-Json
    $found = "$($installed.MajorVersion).$($installed.MinorVersion)"
    if ($found -ne $pinned) {
        Fail "Moteur $found.$($installed.PatchVersion) sous $EnginePath : le dépôt épingle Unreal Engine $pinned (UNREAL_ENGINE_VERSION, ci.yml)."
    }
    Write-Host "Unreal Engine $found.$($installed.PatchVersion) : $EnginePath" -ForegroundColor DarkGray

    $walks = @($Parcours, $ParcoursCombat, $ParcoursDemo) | Where-Object { $_ }
    if ($walks.Count -gt 0 -and $Map) { Fail '-Parcours, -ParcoursCombat et -ParcoursDemo construisent leurs cartes : ils ne se combinent pas avec -Map.' }
    if ($walks.Count -gt 1) { Fail '-Parcours, -ParcoursCombat et -ParcoursDemo se lancent l''un après l''autre.' }
    if ($Ecrans -and ($Map -or $walks.Count -gt 0)) { Fail '-Ecrans construit ses cartes et se lance seul.' }
    $walking = $walks.Count -gt 0
    $roundTrip = -not $Map -and -not $walking -and -not $Ecrans
    if (-not $Map -and -not $NoCapture -and -not $walking -and -not $Ecrans) {
        $Map = $SocleMap
        $Capture = $true
    }

    Write-Host "== UnrealBuildTool : JustAnotherRpgGameEditor Win64 $Configuration ==" -ForegroundColor Cyan
    & $build JustAnotherRpgGameEditor Win64 $Configuration -Project="$uproject" -WaitMutex -NoHotReload
    if ($LASTEXITCODE -ne 0) { Fail "La construction du moteur a échoué (code $LASTEXITCODE)." }

    Write-Host '== Les personnages : mannequin du moteur, créateur Mutable (LOT-1015) ==' -ForegroundColor Cyan
    $python = Join-Path $root '.venv\Scripts\python.exe'
    & $python (Join-Path $root 'scripts\assetsGeneration\import_mannequin_unreal.py') --engine "$EnginePath"
    if ($LASTEXITCODE -ne 0) { Fail "Le mannequin du moteur ne s'est pas posé (code $LASTEXITCODE)." }
    & $editorCmd "$uproject" -run=JadgBuildCharacterCreator -unattended -nosplash -nullrhi -NoSound -stdout -FullStdOutLogOutput
    if ($LASTEXITCODE -ne 0) { Fail "Le créateur de personnage ne s'est pas construit (code $LASTEXITCODE)." }

    Write-Host "== L'interface : images du kit UI et polices (LOT-1020) ==" -ForegroundColor Cyan
    $uiImporter = (Join-Path $root 'scripts\assetsGeneration\import_ui_unreal.py') -replace '\\', '/'
    & $editorCmd "$uproject" -run=pythonscript "-script=$uiImporter" -unattended -nosplash -nullrhi -NoSound -stdout -FullStdOutLogOutput
    if ($LASTEXITCODE -ne 0) { Fail "L'import de l'interface a échoué (code $LASTEXITCODE)." }
    & $editorCmd "$uproject" -run=JadgImportFonts -unattended -nosplash -nullrhi -NoSound -stdout -FullStdOutLogOutput
    if ($LASTEXITCODE -ne 0) { Fail "L'import des polices a échoué (code $LASTEXITCODE)." }

    Write-Host '== Commandlet JadgContentCheck (sans fenêtre) ==' -ForegroundColor Cyan
    & $editorCmd "$uproject" -run=JadgContentCheck -unattended -nosplash -nullrhi -NoSound -stdout -FullStdOutLogOutput
    if ($LASTEXITCODE -ne 0) { Fail "Le contrôle du contenu a échoué (code $LASTEXITCODE)." }

    Write-Host "== Tests d'automatisation du moteur : Jadg (sans fenêtre) ==" -ForegroundColor Cyan
    $report = Join-Path $root 'Saved\Automation\Jadg'
    if (Test-Path $report) { Remove-Item -Recurse -Force $report }
    & $editorCmd "$uproject" '-ExecCmds=Automation RunTests Jadg; Quit' "-ReportExportPath=$report" -unattended -nosplash -nullrhi -NoSound -stdout -FullStdOutLogOutput
    $automationExit = $LASTEXITCODE
    $index = Join-Path $report 'index.json'
    if (-not (Test-Path $index)) { Fail "Les tests d'automatisation n'ont pas écrit leur rapport (code $automationExit) : $index" }
    $results = Get-Content $index -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($test in $results.tests) {
        $colour = if ($test.state -ne 'Success') { 'Red' } elseif ($test.warnings -gt 0) { 'Yellow' } else { 'Green' }
        Write-Host "  $($test.state.PadRight(8)) $($test.fullTestPath)" -ForegroundColor $colour
        foreach ($entry in $test.entries) {
            if ($entry.event.type -ne 'Info') { Write-Host "             $($entry.event.type) : $($entry.event.message)" -ForegroundColor $colour }
        }
    }
    # Un rapport sans test passé serait vert par vacuité : le filtre ne trouverait plus rien.
    $passed = $results.succeeded + $results.succeededWithWarnings
    if ($results.failed -ne 0 -or $results.notRun -ne 0 -or $passed -lt 1 -or $automationExit -ne 0) {
        Fail "Tests d'automatisation : $passed passé(s), $($results.failed) en échec, $($results.notRun) non lancé(s) (code $automationExit). Rapport : $report"
    }
    Write-Host "Tests d'automatisation : $passed passé(s), dont $($results.succeededWithWarnings) avec avertissement." -ForegroundColor Green

    Write-Host '== Les cartes : contrôle des descriptions (jadg_map.py --check) ==' -ForegroundColor Cyan
    & (Get-Python) (Join-Path $root 'scripts\maps\jadg_map.py') --check
    if ($LASTEXITCODE -ne 0) { Fail 'Une carte ne passe pas son contrôle : python scripts/maps/jadg_map.py --check' }
    & (Get-Python) (Join-Path $root 'scripts\maps\build_essai_maps.py') --check
    if ($LASTEXITCODE -ne 0) { Fail "Les cartes d'essai sont périmées : python scripts/maps/build_essai_maps.py" }

    if ($roundTrip) {
        Write-Host "== Les cartes : l'aller-retour entre le texte et l'éditeur (essai/etages) ==" -ForegroundColor Cyan
        $roundTripScript = (Join-Path $root 'scripts\maps\check_level_roundtrip.py') -replace '\\', '/'
        & $editorCmd "$uproject" -run=pythonscript "-script=$roundTripScript" -unattended -nosplash -nullrhi -NoSound -stdout -FullStdOutLogOutput
        if ($LASTEXITCODE -ne 0) { Fail "L'aller-retour d'une carte entre le texte et l'éditeur a échoué (code $LASTEXITCODE)." }
    }

    if ($Parcours) {
        # Les cartes d'essai de l'exploration : une description v5 par carte, écrite par script.
        foreach ($trial in @('essai/etals', 'essai/parvis', 'essai/arene')) { Invoke-LevelBuild $editorCmd $trial }

        $start = (Get-MapInfo 'essai/etals').package
        $output = Join-Path $root 'Saved\Captures\parcours-1016'
        $journal = Join-Path $output 'parcours.json'
        if (Test-Path $journal) { Remove-Item $journal }
        Write-Host "== Parcours : la quête des pommes sur les cartes d'essai (rendu hors écran, graine $Seed) ==" -ForegroundColor Cyan
        & $editorCmd "$uproject" $start -game -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound `
            "-JadgParcours=$output" "-JadgSeed=$Seed" -stdout -FullStdOutLogOutput
        $walked = $LASTEXITCODE
        if (Test-Path $journal) { Get-Content $journal -Encoding UTF8 }
        if ($walked -ne 0) { Fail "Le parcours ne s'est pas terminé (code $walked) : $journal" }
        if (-not (Test-Path $journal)) { Fail "Le parcours n'a pas écrit $journal." }
        Assert-Completed $journal 'Le parcours'
        Write-Host "Parcours terminé : $output" -ForegroundColor Green
        exit 0
    }

    if ($ParcoursDemo) {
        # Les trois lieux de la démo, chacun depuis sa description v5 (LOT-1022).
        $demoMaps = @('central-empire/capital/martpart', 'central-empire/capital/arenarea', 'central-empire/capital/arenarea/arena-of-fate')
        foreach ($demoMap in $demoMaps) { Invoke-LevelBuild $editorCmd $demoMap }

        $start = (Get-MapInfo $demoMaps[0]).package
        $output = Join-Path $root 'Saved\Captures\parcours-demo-1022'
        $journal = Join-Path $output 'parcours.json'
        if (Test-Path $journal) { Remove-Item $journal }
        Write-Host "== Parcours de la démo : de Martpart à l'Arena of Fate et retour (rendu hors écran) ==" -ForegroundColor Cyan
        & $editorCmd "$uproject" $start -game -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound `
            "-JadgParcoursDemo=$output" -stdout -FullStdOutLogOutput
        $walked = $LASTEXITCODE
        if (Test-Path $journal) { Get-Content $journal -Encoding UTF8 }
        if ($walked -ne 0) { Fail "Le parcours de la démo ne s'est pas terminé (code $walked) : $journal" }
        if (-not (Test-Path $journal)) { Fail "Le parcours de la démo n'a pas écrit $journal." }
        Assert-Completed $journal 'Le parcours de la démo'
        Write-Host "Parcours de la démo terminé : $output" -ForegroundColor Green
        exit 0
    }

    if ($Ecrans) {
        # La carte des étals et l'arène d'essai : une description v5 par carte, écrite par script.
        foreach ($trial in @('essai/etals', 'essai/arene')) { Invoke-LevelBuild $editorCmd $trial }
        # L'arène du tour des écrans est celle d'essai : ses captures ont leur référence (LOT-1020).
        $trialArena = "-JadgArene=$((Get-MapInfo 'essai/arene').package)"

        $output = Join-Path $root 'Saved\Captures\ecrans-1020'
        if (Test-Path $output) { Remove-Item -Recurse -Force $output }
        Write-Host '== Les écrans : le tour, au clavier et à la souris, sur les étals (rendu hors écran) ==' -ForegroundColor Cyan
        & $editorCmd "$uproject" (Get-MapInfo 'essai/etals').package -game -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound `
            "-JadgEcrans=$output" -JadgSansRencontre $trialArena "-JadgSeed=$Seed" -stdout -FullStdOutLogOutput
        if ($LASTEXITCODE -ne 0) { Fail "Le tour des écrans ne s'est pas terminé (code $LASTEXITCODE) : $output\ecrans.json" }
        Write-Host "== Les écrans : l'interface du combat, sur l'arène (rendu hors écran) ==" -ForegroundColor Cyan
        & $editorCmd "$uproject" (Get-MapInfo 'essai/arene').package -game -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound `
            "-JadgEcrans=$output" -JadgRencontre=arene-bandits $trialArena "-JadgSeed=$Seed" -stdout -FullStdOutLogOutput
        if ($LASTEXITCODE -ne 0) { Fail "Le tour de l'interface du combat ne s'est pas terminé (code $LASTEXITCODE) : $output\ecrans-combat.json" }

        $reference = Join-Path $root 'Source\Test\Fixtures\Captures\ecrans-1020'
        $compare = Join-Path $root 'scripts\checks\compare_captures.py'
        if ($UpdateReference) {
            Write-Host '== Les écrans : la référence des captures est réécrite ==' -ForegroundColor Yellow
            & (Get-Python) $compare --reference $reference --captures $output --update
            if ($LASTEXITCODE -ne 0) { Fail "La référence des captures des écrans n'a pas pu être écrite (code $LASTEXITCODE)." }
        } else {
            Write-Host '== Les écrans : captures comparées à leur référence ==' -ForegroundColor Cyan
            & (Get-Python) $compare --reference $reference --captures $output
            if ($LASTEXITCODE -ne 0) { Fail "Une capture d'écran s'écarte de sa référence : $reference" }
        }
        Write-Host "Tour des écrans terminé : $output" -ForegroundColor Green
        exit 0
    }

    if ($ParcoursCombat) {
        # Le parvis d'essai et l'Arena of Fate, la carte d'arène du jeu (LOT-1022).
        foreach ($trial in @('essai/parvis', 'central-empire/capital/arenarea/arena-of-fate')) { Invoke-LevelBuild $editorCmd $trial }

        $start = (Get-MapInfo 'essai/parvis').package
        $output = Join-Path $root 'Saved\Captures\parcours-1017'
        $journal = Join-Path $output 'parcours.json'
        if (Test-Path $journal) { Remove-Item $journal }
        Write-Host "== Parcours du combat : arene-bandits depuis le parvis, sur le sable de l'Arena of Fate (rendu hors écran, graine $Seed) ==" -ForegroundColor Cyan
        & $editorCmd "$uproject" $start -game -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound `
            "-JadgParcoursCombat=$output" "-JadgSeed=$Seed" -stdout -FullStdOutLogOutput
        $walked = $LASTEXITCODE
        if ($walked -ne 0) { Fail "Le parcours du combat ne s'est pas terminé (code $walked) : $journal" }
        if (-not (Test-Path $journal)) { Fail "Le parcours du combat n'a pas écrit $journal." }
        Assert-Completed $journal 'Le parcours du combat'
        Write-Host "Parcours du combat terminé : $output" -ForegroundColor Green
        exit 0
    }

    if ($Map) {
        $mapData = Get-MapInfo $Map
        if ($Map -eq 'porte-1012') {
            # La porte et son Colisée sont des sorties de script : le niveau ne se construit pas sur un fichier périmé.
            & (Get-Python) (Join-Path $root 'scripts\maps\build_gate_scene.py') --check
            if ($LASTEXITCODE -ne 0) { Fail 'La porte ou le Colisée sont périmés : python scripts/maps/build_gate_scene.py' }
        }
        if ($Map -like 'controle/*') {
            # La carte de contrôle d'une pièce de décor est une sortie de script (LOT-1019).
            & (Get-Python) (Join-Path $root 'scripts\maps\build_piece_check.py') --check
            if ($LASTEXITCODE -ne 0) { Fail 'Une carte de contrôle de pièce est périmée : python scripts/maps/build_piece_check.py' }
        }
        if ($Map -eq $SocleMap) {
            # Le repère du socle est une donnée d'essai écrite par script : pas de niveau sur un fichier périmé.
            & (Get-Python) (Join-Path $root 'scripts\assetsGeneration\build_mesh_fixture.py') --check
            if ($LASTEXITCODE -ne 0) { Fail "Les données d'essai en maillages sont périmées : python scripts/assetsGeneration/build_mesh_fixture.py" }
        }
        Invoke-LevelBuild $editorCmd $Map

        if ($Capture) {
            $name = $Map -replace '/', '-'
            # Les étages montrés pendant le passage (LOT-1022) : leurs cadrages seuls, leur cadence.
            $shown = @()
            $storeyOption = '-JadgNoop'
            if ($Etages) {
                $shown = @($Etages -split ',' | ForEach-Object { [int]$_.Trim() })
                $storeyOption = "-JadgEtages=$($shown -join ',')"
                $name = "$name-etages-$($shown -join '-')"
            }
            $output = Join-Path $root "Saved\Captures\$name"
            $measureFile = Join-Path $output 'mesure.json'
            if (Test-Path $measureFile) { Remove-Item $measureFile }

            Write-Host "== Carte « $Map » : captures et mesure de cadence (rendu hors écran, 1920 × 1080) ==" -ForegroundColor Cyan
            # Une rencontre engagée au lancement de l'arène : le combat monté, figé sur son déploiement ;
            # la carte capturée est l'arène du passage.
            $engaged = if ($Encounter) { "-JadgRencontre=$Encounter" } else { '-JadgSansRencontre' }
            $arena = if ($Encounter) { "-JadgArene=$($mapData.package)" } else { '-JadgNoop' }
            & $editorCmd "$uproject" $mapData.package -game -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound `
                "-JadgCapture=$output" "-JadgHours=$($mapData.hours -join ',')" "-JadgMeasure=$MeasureSeconds" $engaged $arena $storeyOption "-JadgSeed=$Seed" -stdout -FullStdOutLogOutput
            if ($LASTEXITCODE -ne 0) { Fail "La capture a échoué (code $LASTEXITCODE)." }
            if (-not (Test-Path $measureFile)) { Fail "La capture n'a pas écrit $measureFile." }
            foreach ($shot in $mapData.shots) {
                if ($shown.Count -gt 0 -and $shown -notcontains [int]$shot.storey) { continue }
                foreach ($hour in $mapData.hours) {
                    $image = Join-Path $output "$($shot.id)-$($hour -replace ':', '').png"
                    if (-not (Test-Path $image)) { Fail "Capture absente : $image" }
                }
            }
            Write-Host "Captures et mesure : $output" -ForegroundColor Green
            Get-Content $measureFile

            # Une carte qui a une référence s'y compare, à tolérance et par blocs ; -UpdateReference la réécrit.
            $reference = Join-Path $root "Source\Test\Fixtures\Captures\$name"
            $compare = Join-Path $root 'scripts\checks\compare_captures.py'
            if ($UpdateReference) {
                Write-Host "== Carte « $Map » : la référence des captures est réécrite ==" -ForegroundColor Yellow
                & (Get-Python) $compare --reference $reference --captures $output --update
                if ($LASTEXITCODE -ne 0) { Fail "La référence des captures n'a pas pu être écrite (code $LASTEXITCODE)." }
            } elseif (Test-Path (Join-Path $reference 'reference.json')) {
                Write-Host "== Carte « $Map » : captures comparées à leur référence ==" -ForegroundColor Cyan
                & (Get-Python) $compare --reference $reference --captures $output
                if ($LASTEXITCODE -ne 0) { Fail "Une capture s'écarte de sa référence : $reference" }
            } elseif ($Map -eq $SocleMap) {
                Fail "La carte du socle n'a pas de référence de captures : $reference (-UpdateReference pour l'écrire)."
            }
        }
    }
    exit 0
}

$vs = Find-VisualStudio
$binaryDir = Join-Path $root "build\$Preset"
if ($Clean -and (Test-Path $binaryDir)) { Remove-Item -Recurse -Force $binaryDir }

Write-Host "== Tests de Core hors moteur : preset $Preset (Visual Studio : $vs) ==" -ForegroundColor Cyan
Invoke-InMsvcEnvironment $vs "cmake --preset $Preset && cmake --build --preset $Preset && ctest --preset $Preset"
exit 0
