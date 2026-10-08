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
        4. la carte d'une scène est reconstruite par script depuis sa description ;
        5. le jeu est lancé hors écran sur cette carte, ses captures sont prises, puis comparées
           à tolérance à leur référence si la scène en a une (Source/Test/Fixtures/Captures/).
      Sans -Scene, la scène est celle du socle (socle-1014) : elle ne lit aucun kit d'assets, ses
      captures ont une référence, et les temps 4 et 5 se font d'office. -NoCapture les saute, sur
      un poste sans processeur graphique.
      Le moteur est trouvé par l'association du .uproject (registre HKCU\Software\Epic Games\
      Unreal Engine\Builds), ou par -EnginePath ; sa version doit être celle que ci.yml épingle
      (UNREAL_ENGINE_VERSION).

.PARAMETER Unreal
    Construire le projet Unreal, contrôler le contenu, lancer les tests d'automatisation, puis
    construire la scène du socle et comparer ses captures à leur référence.

.PARAMETER Scene
    Avec -Unreal : construire la carte de cette description de scène
    (Source/Elements/Scenes/<Scene>.json) par scripts/maps/build_scene_unreal.py, sans fenêtre
    (LOT-1012), à la place de celle du socle. Ses captures ne se prennent qu'avec -Capture.

.PARAMETER Capture
    Avec -Scene : lancer ensuite le jeu hors écran sur cette carte, prendre les captures aux
    cadrages et aux heures de la description, mesurer la cadence, et vérifier que chaque image est
    écrite. Sorties dans Saved/Captures/<Scene>/. Demande un processeur graphique.

.PARAMETER NoCapture
    Avec -Unreal, sans -Scene : ne pas construire la scène du socle ni prendre ses captures.

.PARAMETER UpdateReference
    Avec des captures : réécrire leur référence (les images de blocs de
    Source/Test/Fixtures/Captures/<Scene>/) au lieu de les y comparer. Pour une image qui a changé
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
    Construit l'éditeur du projet, vérifie le contenu, lance les tests du moteur, reconstruit la
    carte du socle et compare ses captures à leur référence, sans fenêtre.

.EXAMPLE
    pwsh scripts/build.ps1 -Unreal -Scene porte-1012 -Capture
    Construit, vérifie, reconstruit la carte de la porte, puis en prend les captures et la mesure.
#>
[CmdletBinding()]
param(
    [switch]$Unreal,
    [string]$Scene,
    [switch]$Capture,
    [switch]$NoCapture,
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

# La scène que -Unreal construit et capture d'office : elle ne lit aucun kit d'assets (LOT-1014).
$SocleScene = 'socle-1014'

function Get-Python {
    # L'environnement du dépôt (uv sync) s'il existe : ses versions sont celles de uv.lock.
    $venv = Join-Path $root '.venv\Scripts\python.exe'
    if (Test-Path $venv) { return $venv }
    return 'python'
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

    if (-not $Scene -and -not $NoCapture) {
        $Scene = $SocleScene
        $Capture = $true
    }

    Write-Host "== UnrealBuildTool : JustAnotherRpgGameEditor Win64 $Configuration ==" -ForegroundColor Cyan
    & $build JustAnotherRpgGameEditor Win64 $Configuration -Project="$uproject" -WaitMutex -NoHotReload
    if ($LASTEXITCODE -ne 0) { Fail "La construction du moteur a échoué (code $LASTEXITCODE)." }

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

    if ($Scene) {
        $description = Join-Path $root "Source\Elements\Scenes\$Scene.json"
        if (-not (Test-Path $description)) { Fail "Description de scène absente : $description" }

        if ($Scene -eq 'porte-1012') {
            # Le groupe du Colisée est une sortie de script : la carte ne se construit pas sur un fichier périmé.
            & (Get-Python) (Join-Path $root 'scripts\maps\build_gate_scene.py') --check
            if ($LASTEXITCODE -ne 0) { Fail 'Le groupe du Colisée (colisee.json) est périmé : python scripts/maps/build_gate_scene.py' }
        }
        if ($Scene -eq $SocleScene) {
            # Le repère du socle est une donnée d'essai écrite par script : pas de carte sur un fichier périmé.
            & (Get-Python) (Join-Path $root 'scripts\assetsGeneration\build_mesh_fixture.py') --check
            if ($LASTEXITCODE -ne 0) { Fail "Les données d'essai en maillages sont périmées : python scripts/assetsGeneration/build_mesh_fixture.py" }
        }

        Write-Host "== Scène « $Scene » : construction de la carte par script (sans fenêtre) ==" -ForegroundColor Cyan
        # Chemin absolu : le moteur résout un chemin relatif depuis son propre dossier de binaires.
        $builder = (Join-Path $root 'scripts\maps\build_scene_unreal.py') -replace '\\', '/'
        & $editorCmd "$uproject" -run=pythonscript "-script=$builder" "-JadgScene=$Scene" -unattended -nosplash -nullrhi -NoSound -stdout -FullStdOutLogOutput
        if ($LASTEXITCODE -ne 0) { Fail "La construction de la scène a échoué (code $LASTEXITCODE)." }

        if ($Capture) {
            $sceneData = Get-Content $description -Raw -Encoding UTF8 | ConvertFrom-Json
            $output = Join-Path $root "Saved\Captures\$Scene"
            $measureFile = Join-Path $output 'mesure.json'
            if (Test-Path $measureFile) { Remove-Item $measureFile }

            Write-Host "== Scène « $Scene » : captures et mesure de cadence (rendu hors écran, 1920 × 1080) ==" -ForegroundColor Cyan
            & $editorCmd "$uproject" $sceneData.map -game -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -unattended -nosplash -NoSound `
                "-JadgCapture=$output" "-JadgHours=$($sceneData.hours -join ',')" "-JadgMeasure=$MeasureSeconds" -stdout -FullStdOutLogOutput
            if ($LASTEXITCODE -ne 0) { Fail "La capture a échoué (code $LASTEXITCODE)." }
            if (-not (Test-Path $measureFile)) { Fail "La capture n'a pas écrit $measureFile." }
            foreach ($shot in $sceneData.shots) {
                foreach ($hour in $sceneData.hours) {
                    $image = Join-Path $output "$($shot.id)-$($hour -replace ':', '').png"
                    if (-not (Test-Path $image)) { Fail "Capture absente : $image" }
                }
            }
            Write-Host "Captures et mesure : $output" -ForegroundColor Green
            Get-Content $measureFile

            # Une scène qui a une référence s'y compare, à tolérance et par blocs ; -UpdateReference la réécrit.
            $reference = Join-Path $root "Source\Test\Fixtures\Captures\$Scene"
            $compare = Join-Path $root 'scripts\checks\compare_captures.py'
            if ($UpdateReference) {
                Write-Host "== Scène « $Scene » : la référence des captures est réécrite ==" -ForegroundColor Yellow
                & (Get-Python) $compare --reference $reference --captures $output --update
                if ($LASTEXITCODE -ne 0) { Fail "La référence des captures n'a pas pu être écrite (code $LASTEXITCODE)." }
            } elseif (Test-Path (Join-Path $reference 'reference.json')) {
                Write-Host "== Scène « $Scene » : captures comparées à leur référence ==" -ForegroundColor Cyan
                & (Get-Python) $compare --reference $reference --captures $output
                if ($LASTEXITCODE -ne 0) { Fail "Une capture s'écarte de sa référence : $reference" }
            } elseif ($Scene -eq $SocleScene) {
                Fail "La scène du socle n'a pas de référence de captures : $reference (-UpdateReference pour l'écrire)."
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
