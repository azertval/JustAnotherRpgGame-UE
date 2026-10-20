# Core · Resources

Tests unitaires — **11 cas** (5 bloquants, 6 majeurs). [Retour à la synthèse](README.md).

## Ce que cette page couvre

| Fichier de test | Cas | Bloquant | Critique | Majeur | Mineur |
|---|---|---|---|---|---|
| [`test_scene_piece_manifest.cpp`](#test-scene-piece-manifestcpp) | 3 | 2 | - | 1 | - |
| [`test_scene_place.cpp`](#test-scene-placecpp) | 8 | 3 | - | 5 | - |

## test_scene_piece_manifest.cpp

### ScenePieceManifestTest.LeManifesteDUnLieuSeLit

*Bloquant · Unitaire · Assets* — `Source/Test/Unit/Core/Resources/test_scene_piece_manifest.cpp:29`

Le manifeste des pieces d'un lieu se lit dans Core.

**Étapes**

1. Lire le manifeste du lieu d'essai.
2. Chercher une piece de sol, une piece large et son miroir.

**Résultat attendu**

- Vérifie que `read.ok()` est vrai.
- Vérifie que `manifest.place()` vaut `"bourg"`.
- Vérifie que `manifest.pieces().empty()` est faux.
- Vérifie que `street` diffère de `nullptr`.
- Vérifie que `street->key` vaut `"scene/bourg/street"`.
- Vérifie que `street->file` vaut `"street.png"`.
- Vérifie que `street->pieceClass` vaut `core::ScenePieceClass::Floor`.
- Vérifie que `street->footprintColumns` vaut `1`.
- Vérifie que `street->footprintRows` vaut `1`.
- Vérifie que `street->width` vaut `68`.
- Vérifie que `street->height` vaut `42`.
- Vérifie que `street->anchorX` vaut `34`.
- Vérifie que `street->anchorY` vaut `0`.
- Vérifie que `street->mirrorOf.empty()` est vrai.
- Vérifie que `front` diffère de `nullptr`.
- Vérifie que `front->pieceClass` vaut `core::ScenePieceClass::Wide`.
- Vérifie que `front->footprintColumns` vaut `2`.
- Vérifie que `front->footprintRows` vaut `1`.
- Vérifie que `front->mirrorOf` vaut `"front-left"`.
- Vérifie que `manifest.find(front->mirrorOf)` diffère de `nullptr`.
- Vérifie que `manifest.find("piece-inconnue")` vaut `nullptr`.

### ScenePieceManifestTest.ChaquePieceDeclareeASonImage

*Bloquant · Unitaire · Assets* — `Source/Test/Unit/Core/Resources/test_scene_piece_manifest.cpp:73`

Toute piece declaree par un lieu a son image.

**Étapes**

1. Lire les manifestes des deux lieux d'essai.
2. Chercher le fichier de chaque piece dans le dossier du lieu.

**Résultat attendu**

- Vérifie que `read.ok()` est vrai.
- Vérifie que `std::filesystem::is_regular_file(sceneDirectory(place) / piece.file)` est vrai.
- Vérifie que `piece.footprintColumns` est supérieur ou égal à `1`.
- Vérifie que `piece.footprintRows` est supérieur ou égal à `1`.

### ScenePieceManifestTest.UneEntreeFautiveNeFaitPasPerdreLesAutres

*Majeur · Unitaire · Assets* — `Source/Test/Unit/Core/Resources/test_scene_piece_manifest.cpp:98`

Le manifeste des pieces tolere une entree fautive sans perdre les autres.

**Étapes**

1. Lire un manifeste dont une entree n'a pas d'image et une autre une classe inconnue.
2. Lire un manifeste sans `textures`, puis un fichier absent.

**Résultat attendu**

- Vérifie que `read.ok()` est vrai.
- Vérifie que `read.manifest.pieces().size()` vaut `1U`.
- Vérifie que `piece.name` vaut `"estrade"`.
- Vérifie que `piece.pieceClass` vaut `core::ScenePieceClass::Other`.
- Vérifie que `piece.className` vaut `"podium"`.
- Vérifie que `piece.footprintColumns` vaut `1`.
- Vérifie que `piece.footprintRows` vaut `1`.
- Vérifie que `core::ScenePieceManifest::loadFromString(R"({"version": 1})").error` vaut `core::ScenePieceManifestError::MalformedStructure`.
- Vérifie que `core::ScenePieceManifest::loadFromFile(sceneDirectory("absent") / "manifest.json").error` vaut `core::ScenePieceManifestError::FileNotFound`.

## test_scene_place.cpp

### ScenePlaceTest.LesNiveauxDUneSousZoneVontJusquAuMonde

*Bloquant · Unitaire · Assets · Arborescence* — `Source/Test/Unit/Core/Resources/test_scene_place.cpp:44`

Les niveaux d'un lieu vont de la sous-zone au monde.

**Étapes**

1. Demander les niveaux candidats de `central-empire/capital/arenarea/arena-of-fate`.

**Résultat attendu**

- Vérifie que `directoriesOf(levels)` vaut `(std::vector<std::string>{ "Regions/central-empire/capital/arenarea/arena-of-fate/Scene", "Regions/central-empire/capital/arenarea/arena-of-fate/Common/Scene", "Regions/central-empire/capital/arenarea/Scene", "Regions/central-empire/capital/arenarea/Common/Scene", "Regions/central-empire/capital/Scene", "Regions/central-empire/capital/Common/Scene", "Regions/central-empire/Common/Scene", "Common/Terrain", "Common/Nature", "Common/Props", })`.
- Vérifie que `levels.front().label` vaut `"Arena of Fate"`.
- Vérifie que `levels.front().place` vaut `"central-empire/capital/arenarea/arena-of-fate"`.
- Vérifie que `levels[5].label` vaut `"Capital"`.
- Vérifie que `levels[5].place` vaut `"central-empire/capital"`.
- Vérifie que `levels[6].label` vaut `"Central Empire"`.
- Vérifie que `levels.back().label` vaut `"World"`.
- Vérifie que `levels.back().place.empty()` est vrai.

### ScenePlaceTest.UnLieuAPlatEtUnLieuMalForme

*Majeur · Unitaire · Assets · Arborescence* — `Source/Test/Unit/Core/Resources/test_scene_place.cpp:81`

Un lieu a plat et un lieu mal forme.

**Étapes**

1. Demander les niveaux de `bourg`, puis de lieux vides ou contenant `..`.

**Résultat attendu**

- Vérifie que `levels.size()` vaut `4U`.
- Vérifie que `levels.front().directory` vaut `"Scene/bourg"`.
- Vérifie que `levels.front().label` vaut `"Bourg"`.
- Vérifie que `core::fallbackScenePiecePath("bourg", "street")` vaut `"Scene/bourg/street.png"`.
- Vérifie que `core::fallbackScenePiecePath(ARENAREA, "stall")` vaut `"Regions/central-empire/capital/arenarea/Scene/stall.png"`.
- Vérifie que `core::isValidScenePlace(bad)` est faux.
- Vérifie que `core::sceneLevelCandidates(bad).empty()` est vrai.
- Vérifie que `core::fallbackScenePiecePath(bad, "x").empty()` est vrai.

### ScenePlaceTest.UnLieuDescendDeSesPrefixes

*Majeur · Unitaire · Assets · Arborescence* — `Source/Test/Unit/Core/Resources/test_scene_place.cpp:106`

Un lieu descend de ses prefixes et du monde.

**Étapes**

1. Comparer des lieux a leurs prefixes, et lister la filiation d'une zone.

**Résultat attendu**

- Vérifie que `core::scenePlaceDescendsFrom(ARENAREA, "central-empire/capital")` est vrai.
- Vérifie que `core::scenePlaceDescendsFrom(ARENAREA, ARENAREA)` est vrai.
- Vérifie que `core::scenePlaceDescendsFrom(ARENAREA, "")` est vrai.
- Vérifie que `core::scenePlaceDescendsFrom(ARENAREA, "central-empire/capital/martpart")` est faux.
- Vérifie que `core::scenePlaceDescendsFrom(ARENAREA, "central-empire/cap")` est faux.
- Vérifie que `core::scenePlaceAncestry(ARENAREA)` vaut `(std::vector<std::string>{ARENAREA, "central-empire/capital", "central-empire", ""})`.
- Vérifie que `core::scenePlaceAncestry("bourg")` vaut `(std::vector<std::string>{"bourg", ""})`.

### ScenePlaceTest.LeCatalogueDUnLieuEmpileSesNiveaux

*Bloquant · Unitaire · Assets · Arborescence* — `Source/Test/Unit/Core/Resources/test_scene_place.cpp:128`

Le catalogue d'un lieu empile ses niveaux.

**Étapes**

1. Resoudre le lieu `central-empire/capital/arenarea` de la racine LevelTree.

**Résultat attendu**

- Vérifie que `read.ok()` est vrai.
- Vérifie que `catalog.place()` vaut `ARENAREA`.
- Vérifie que `catalog.tileWidth()` vaut `68`.
- Vérifie que `piece` diffère de `nullptr`.
- Vérifie que `piece->level` vaut `expected.level`.
- Vérifie que `piece->path()` vaut `expected.path`.
- Vérifie que `std::filesystem::is_regular_file(treeAssets() / piece->path())` est vrai.
- Vérifie que `catalog.find("sand")` vaut `nullptr`.
- Vérifie que `catalog.masked().size()` vaut `1U`.
- Vérifie que `catalog.masked().front().piece.name` vaut `"fountain"`.
- Vérifie que `catalog.masked().front().piece.level` vaut `"Capital"`.
- Vérifie que `catalog.masked().front().by` vaut `"Arenarea"`.
- Vérifie que `std::ranges::count(catalog.pieces(), std::string{"fountain"}, &core::ScenePiece::name)` vaut `1`.
- Vérifie que `levels` vaut `(std::vector<std::string>{"Arenarea", "Capital", "Central Empire", "World", "World"})`.

### ScenePlaceTest.UneZoneSansPieceProprePuiseDansLaVille

*Majeur · Unitaire · Assets · Arborescence* — `Source/Test/Unit/Core/Resources/test_scene_place.cpp:189`

Une zone sans piece propre puise dans la ville.

**Étapes**

1. Resoudre `central-empire/capital/martpart`.

**Résultat attendu**

- Vérifie que `read.ok()` est vrai.
- Vérifie que `fountain` diffère de `nullptr`.
- Vérifie que `fountain->directory` vaut `"Regions/central-empire/capital/Common/Scene"`.
- Vérifie que `read.manifest.masked().empty()` est vrai.

### ScenePlaceTest.LArbreDesLieuxListeLesZones

*Majeur · Unitaire · Assets · Arborescence* — `Source/Test/Unit/Core/Resources/test_scene_place.cpp:208`

L'arbre des lieux liste les zones et sous-zones.

**Étapes**

1. Lister les lieux de la racine LevelTree.

**Résultat attendu**

- Vérifie que `core::scenePlaces(treeAssets())` vaut `(std::vector<std::string>{ARENAREA, "central-empire/capital/arenarea/arena-of-fate", "central-empire/capital/martpart"})`.

### ScenePlaceTest.UnNiveauCommunIllisibleFaitEchouerLaResolution

*Majeur · Unitaire · Assets · Arborescence* — `Source/Test/Unit/Core/Resources/test_scene_place.cpp:225`

Un niveau commun illisible fait echouer la resolution.

**Étapes**

1. Ecrire une zone lisible sous une ville dont le manifeste est casse, et la resoudre.
2. Resoudre un lieu qui n'a aucun manifeste.

**Résultat attendu**

- Vérifie que `broken.ok()` est faux.
- Vérifie que `broken.message.find("Regions/r/v/Common/Scene/manifest.json")` diffère de `std::string::npos`.
- Vérifie que `none.error` vaut `core::ScenePieceManifestError::FileNotFound`.

### ScenePlaceTest.LesFiguresDUnLieuViennentDeSesNiveaux

*Bloquant · Unitaire · Assets · Arborescence* — `Source/Test/Unit/Core/Resources/test_scene_place.cpp:259`

Les figurines d'un lieu viennent de ses niveaux.

**Étapes**

1. Lister les niveaux de figurines de l'Arenarea.
2. Resoudre ses figurines, puis celles du Martpart.
3. Demander le dossier d'une figurine inconnue, d'un chemin, d'un slug seul.

**Résultat attendu**

- Vérifie que `directories` vaut `(std::vector<std::string>{ "Regions/central-empire/capital/arenarea/Characters", "Regions/central-empire/capital/arenarea/Common/Characters", "Regions/central-empire/capital/Characters", "Regions/central-empire/capital/Common/Characters", "Regions/central-empire/Common/Characters", "Common/Characters", })`.
- Vérifie que `core::characterLevelCandidates("bourg").size()` vaut `1U`.
- Vérifie que `core::figureDirectory(arena, "anariel")` vaut `"Regions/central-empire/capital/arenarea/Characters/anariel"`.
- Vérifie que `core::figureDirectory(arena, "citizen")` vaut `"Regions/central-empire/capital/arenarea/Characters/citizen"`.
- Vérifie que `core::figureDirectory(arena, "Peoples/human/guard")` vaut `"Common/Characters/Peoples/human/guard"`.
- Vérifie que `std::filesystem::is_regular_file(treeAssets() / directory / "character.json")` est vrai.
- Vérifie que `core::figureDirectory(mart, "citizen")` vaut `"Regions/central-empire/capital/Common/Characters/citizen"`.
- Vérifie que `mart.contains("anariel")` est faux.
- Vérifie que `core::figureDirectory({}, "Monsters/lion")` vaut `"Monsters/lion"`.
- Vérifie que `core::figureDirectory({}, "figurant")` vaut `"Npc/figurant"`.
- Vérifie que `core::figureDirectory({}, "")` vaut `""`.
