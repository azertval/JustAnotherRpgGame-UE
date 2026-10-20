param([string]$SourceProject='E:\JustAnotherRpgGame_UR\BlendMasterMaterial')
$ErrorActionPreference='Stop'
$projectRoot=Split-Path (Split-Path $PSScriptRoot)
$sourceContent=Join-Path $SourceProject 'Content'
$destinationContent=Join-Path $projectRoot 'Content'
# Preserve package paths and reject collisions rather than overwrite another library.
foreach ($file in Get-ChildItem -LiteralPath $sourceContent -Recurse -File) {
    $relative=$file.FullName.Substring($sourceContent.Length+1)
    $target=Join-Path $destinationContent $relative
    if (Test-Path -LiteralPath $target) {
        if ((Get-FileHash -LiteralPath $target).Hash -ne (Get-FileHash -LiteralPath $file.FullName).Hash) { throw "Different existing asset: $relative" }
    } else {
        New-Item -ItemType Directory -Path (Split-Path $target) -Force | Out-Null
        Copy-Item -LiteralPath $file.FullName -Destination $target
    }
}
Write-Output 'Sensei library installed. Run build_aof_surface_v2.py, then build_aof_pilot_scene.py in Unreal.'
