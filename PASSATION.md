# Passation : de l'ancien dépôt au nouveau moteur

Le 7 octobre 2026, le jeu passe sur Unreal Engine 5 ([D-48](Planning/vision/decisions.md)) et
change de dépôt ([D-58](Planning/vision/decisions.md)). Cette page dit ce qui est venu de
`D:\JustAnotherDnDGame` (le dépôt du moteur maison, à l'état du commit `f4edf6d18`, PR #182), ce qui
y est resté, et pourquoi. Elle est le premier livrable du
[LOT-1014](Planning/versions/v0.1.0/v0.0.3-nouveau-moteur/lots/LOT-1014-socle-core-donnees-build.md).

## Ce qui est venu

| Quoi | Où, dans ce dépôt | Remarques |
|---|---|---|
| `Source/Core` — les règles d20, les classes, les capacités, les quêtes, les dialogues, le monde (85 `.cpp`, 113 `.h`) | `Source/JustAnotherRpgGame/Core/` | **Copié tel quel, sans une ligne modifiée.** Les inclusions `"Core/<Module>/<Fichier>.h"` se résolvent depuis la racine du module. Voir « Core dans le module du jeu » |
| nlohmann/json 3.11.3 (MIT) | `Source/ThirdParty/nlohmann/` | L'en-tête unique et sa licence, vendus : le moteur n'a pas de FetchContent |
| Les données de contenu : `Rpg/`, `World/`, `Levels/`, `Maps/`, `Localization/`, `Credits/`, `Editor/` | `Source/Elements/` | Les 721 fichiers suivis par Git (le dépôt en comptait 486 hors polices, manifestes et fiches de carte ; tous sont venus). Les kits d'assets (images, maillages, 2,2 Go hors Git) se réinstallent par `scripts/fetch_assets.py` d'après `kits.lock.json`, qui est venu |
| Les tests unitaires de Core (89 fichiers, 88 compilés), leurs fixtures | `Source/Test/Unit/Core/`, `Source/Test/Fixtures/` | Construits hors du moteur par `CMakeLists.txt` à la racine ; voir « Les tests de Core » |
| `Planning/` (429 fichiers) | `Planning/` | Tel quel : versions, lots, standards, décisions, référentiels |
| `Documentation/` (169 fichiers) | `Documentation/` | Venu tel quel ; ce qui ne décrivait que le moteur maison est supprimé le 8 octobre (D-59), voir « Ce qui reste à faire » |
| `scripts/` (assets, checks, docs, i18n, maps, release, sourcebook, tests) | `scripts/` | Sans les quatre contrôles propres à QML ni l'épingle de version Qt, voir ci-dessous |
| `LICENSE`, `LICENSE-CONTENT`, `THIRD-PARTY-NOTICES.md`, `CHANGELOG.md`, `CONTRIBUTING.md` | racine | Le CHANGELOG continue à la `0.0.3` ; `CONTRIBUTING.md` et `THIRD-PARTY-NOTICES.md` sont à relire (ils citent Qt) |
| `.editorconfig`, `.clang-format`, `.clang-tidy`, `.clangd`, `pyproject.toml`, `ruff.toml`, `uv.lock`, `.pre-commit-config.yaml`, `lychee.toml` | racine | Tels quels ; `.pre-commit-config.yaml` cite des contrôles qui n'existent plus ici, à relire au LOT-1014 (CI) |

## Les maillages au maître (`D:\Telechargement\Assets`, 7 octobre 2026)

L'auteur a livré 71 retours Meshy au maître — 22 statues de dieux, 22 PNJ, 27 armes —, 2,7 Go,
78 millions de triangles, entre 49 000 (une lance) et 2,9 millions (le Roi forgé-lion). Aucun
n'est riggé ; chacun porte une matière et trois images. Le moteur n'étant pas borné en triangles
(Nanite), ils entrent tels quels (D-53) :

- `scripts/assetsGeneration/build_master_manifest.py` les range sous
  `Source/Elements/Assets/Master/{Statues,Npc,Weapons}/` avec un identifiant lisible, et écrit
  `manifest.json` (suivi par Git) : famille, fichier source, empreinte SHA-256, triangles, sommets,
  images, asset produit. Les pièces portent le nom de leur **référence** (`references.json`, 8 octobre) :
  les 22 statues par les deux relevés d'identification de l'atelier (`V2/MeshyReferences/meshy-identification.json`,
  `V3/Sculptures/identification.json`, confiance haute), les 21 PNJ par le retour Meshy rangé dans leur fiche
  (`Tools/Assets3D/Personnages/`), les 26 armes par vignettes Blender comparées à la planche `apercu.jpg` ;
  six attributions d'armes et le nom d'une façade restent **à confirmer par l'auteur**, marquées dans la table.
  Un doublon exact (`Runebreaker_Hammer (1)`) est écarté et nommé ; les
  variantes de même nom (`Ironwood_Spear` ×3, `Ironwood_Hatchet` ×2, `Ironclad_Sentinel` ×2)
  gardent l'identifiant Meshy en suffixe. 70 pièces.
- `scripts/assetsGeneration/import_master_unreal.py` (Python d'éditeur, commandlet `pythonscript`,
  sans fenêtre) importe chaque pièce par Interchange sous `Content/Master/<Famille>/<Pièce>/`
  (StaticMeshes/, Materials/, Textures/), Nanite construit à l'import, vérifie l'empreinte avant,
  et sort en erreur à la première pièce fautive. Rejoué, il ne réimporte rien.
- Les PNJ sont importés en maillages **statiques**, pour les voir dans le moteur : leur liaison au
  squelette et leurs clips sont le LOT-1015 (`import_character_unreal.py`), qui remplacera ces
  assets.

## Ce qui est resté dans l'ancien dépôt

Rien de ce qui suit n'est entré, et rien ne doit entrer (D-58 : « rien de Qt n'entre dans le
nouveau ») :

- `Source/HMI` (rendu QRhi, chargeur glTF, audio, entrées, présentation, runtime), `Source/Ui`
  (149 fichiers QML), `Source/App`, `Source/Editor` (le LevelEditor), `Source/Fuzz`,
  `Source/Benchmark`, `Source/pch.h` ;
- `Source/Test/Unit/HMI`, `Source/Test/Unit/Editor`, `Source/Test/Integration`,
  `Source/Test/Systeme`, `Source/Test/Qml`, et deux fichiers de `Source/Test/Support`
  (`ArenaSimulation.h`, `HdMockupScene.h`) qui incluent `HMI/` ; `Source/Test/Unit/Core/Rpg/test_dialogue.cpp`
  est venu mais **n'est pas compilé** : il lit la localisation par `HMI/Localization` ;
- `External/` (FetchContent de GoogleTest, nlohmann, Benchmark), `CMakeLists.txt` et
  `CMakePresets.json` de l'ancien dépôt, remplacés ici par une construction réduite à Core ;
- `.github/` : la CI se refait à neuf (D-58, LOT-1014), elle ne se copie pas ;
- `Site/` (le site public de l'ancien dépôt), `codecov.yml`, `renovate.json` ;
- `scripts/checks/check_qml_designer_compat.py`, `check_ui_layers.py`, `check_ui_assets.py`,
  `scripts/i18n/list_pending_bindings.py` (ils lisent du QML), `scripts/ci/check_qt_version_pin.py`,
  `scripts/build.ps1` et `scripts/coverage.ps1` (Qt, CMake de l'ancien projet) ; `build.ps1` est
  réécrit ici ;
- `Tools/` (ateliers locaux, hors Git), `build/`, `reports/`, `research_notes/`, `.tmp/` ;
- l'histoire Git : ce dépôt commence à la `0.0.3`, l'ancien reste lisible en privé.

## Core dans le module du jeu

Le LOT-1014 prévoyait un module Unreal `Core` à part. Il n'y en a pas, pour une raison de
construction : dans une cible d'éditeur, chaque module est une DLL, et un module séparé aurait
exigé une macro d'export (`JADGCORE_API`) sur chacune des classes de Core — la réécriture que la
passation interdit. Core vit donc **dans** le module `JustAnotherRpgGame`, compilé par ses règles
(`Source/JustAnotherRpgGame/JustAnotherRpgGame.Build.cs`) :

- `bEnableExceptions` et `bUseRTTI` : nlohmann signale par exception, `Core/Ecs/World.h` range
  ses composants par `typeid` ; le moteur compile sans l'un ni l'autre par défaut ;
- `PCHUsage = NoPCHs`, `bUseUnity = false` : sans cela le moteur injecte ses en-têtes — et ses
  macros `check`, `verify`, `ensure` — dans les unités de Core. `Core/Combat/BattleGrid.h` déclare
  une méthode `check(...)` : un fichier du jeu qui l'inclurait **après** un en-tête du moteur ne
  compilerait pas. La règle, dans le code du pont : *Core avant le moteur* dans l'ordre des
  inclusions. `BattleGrid` disparaît au LOT-1017 (combat en distance) ;
- les avertissements d'ombrage et d'identifiant non défini sont des avertissements, pas des
  erreurs, le temps de la passation ; la construction du 7 octobre n'en émet aucun ;
- `JADG_VERSION="0.0.3"` est défini dans le `Build.cs` : le numéro de version a quitté le
  `project()` de CMake, il n'a pas encore retrouvé sa source unique (voir ci-dessous).

Le module ne compte que ce que le moteur impose : `Bridge/JadgPaths` (où sont les données, les
conversions de chaînes), `Bridge/JadgLog` (le journal de Core relayé vers `LogJadg`) et le
commandlet `JadgContentCheck`. Rien d'autre n'a été écrit.

## Ce qui a été vérifié le 7 octobre 2026

| Vérification | Résultat |
|---|---|
| `Build.bat JustAnotherRpgGameEditor Win64 Development` | 94 actions, 109 s, 0 erreur, 0 avertissement |
| `UnrealEditor-Cmd.exe JustAnotherRpgGame.uproject -run=JadgContentCheck -nullrhi` | code 0 ; 22 espèces, 13 historiques, 4 classes lus ; les quatre fiches du groupe préformé de D-28 construites sans erreur : Grom (PV 15, CA 14), Faelar (PV 8, CA 12), Helga (PV 12, CA 11), Nessa (PV 10, CA 13) |
| Tests de Core hors moteur (`scripts/build.ps1`, CMake + Ninja, MSVC 14.51, Debug) | 629 tests, 100 % passés, 1 ignoré (`MeshFileTest.LesModelesReelsDeLAtelierSeLisent`, sans dossier de modèles) ; 1 test écarté par filtre, `FamillesDEntitesTest.ToutFamilleLueParLeJeuEstDansLaTable`, qui balaie `Source/HMI` et `Source/App` ; `test_dialogue.cpp` non compilé (voir ci-dessus) |

Les valeurs attendues des fiches restent dans `Source/Test/Unit/Core/Rpg/test_premade_characters.cpp` ;
le commandlet montre que le moteur lit **les mêmes fichiers** et obtient **des fiches sans erreur**.

## Ce qui reste à faire (LOT-1014)

- **Le dépôt Git** : fait le 8 octobre 2026. Le dépôt est **public**. `Content/` n'est pas suivi
  (D-60) : 3,3 Go de `.uasset` et de `.umap` que le quota LFS d'un compte gratuit ne tient pas, et
  que les scripts du dépôt régénèrent. Le passage de l'ancien dépôt en privé est fait.
- **Ni livre source ni texte extrait** dans le dépôt public (EX-CNT-023) : l'étude des métiers
  (`Documentation/Metiers/`) en portait trois copies — le corpus par livre, le lecteur plein texte,
  le cache de l'atelier —, écartées par `.gitignore` avec la copie de l'atelier ; le site rendu et les trois fichiers au-delà
  de 5 Mio sont suivis, ces derniers en Git LFS. `scripts/checks/check_no_sourcebook.py` refuse, avant le commit
  et en CI, un livre numérique ou un fichier qui a la forme d'une extraction. Les pages
  `Documentation/Metiers/Sources/` gardent leurs liens vers ces fichiers, qui ne mènent plus nulle
  part dans le dépôt : à reprendre par leur générateur.
- **La CI** : refaite à neuf (`.github/workflows/`). Sur les runners hébergés, à chaque PR : les
  tests de Core hors moteur en Debug et en Release, clang-format sur Core et ses tests, douze
  contrôles du référentiel, les hooks, le CHANGELOG. La construction du moteur, ses tests et ses
  captures se vérifient sur le poste avant chaque PR (`scripts/build.ps1 -Unreal`) : `unreal.yml`
  est écrit mais dormant, sans runner auto-hébergé pour l'instant (D-61). Ne sont pas repris tant
  que leur script n'est pas relu : `lint_planning` (un lien vers `Site/README.md`), `lint_docs`
  (des liens vers l'ancien chemin de Core et vers `Source/HMI`), `generate_cahier_test` ;
  `check_map_assets` et `check_hd_assets` lisent les kits, qui se publient sur ce dépôt à la
  `0.0.3` (D-62). Restent à refaire : la publication d'une version, la référence Doxygen et la
  page qualité du site (republié sans elles par `docs.yml`).
- **`Documentation/`** : ce qui ne décrivait que le moteur maison est **supprimé** (D-59, 8 octobre ;
  fiche du LOT-1014, « Rien d'hérité ») : dix guides, le Manuel, vingt-cinq images. Restent à
  reprendre, exigence par exigence : les spécifications `rendu-technique.md`, `interface-ihm.md`,
  `editeur-niveaux.md`, `controles.md` et `architecture.md`, qui déclarent des exigences que Core
  cite encore, et le cahier de tests, dont le générateur décrit des étages restés dans l'ancien
  dépôt.
- **`scripts/`**, relu le 8 octobre (fiche du LOT-1014, « Avancement ») : `check_orphans.py` ne
  connaît plus le `.qml` ni les arbres de l'ancien dépôt et lit `Content/` ; `check_tool_pins.py`
  épingle le moteur ; `check_binary_files.py` refuse une sortie du moteur hors de Git LFS ;
  `setup_dev.ps1` vérifie le moteur à la place de Qt. Neuf scripts que seul l'ancien moteur
  faisait tourner sont supprimés (D-59 : `receive_ui_assets.py`, `check_assets_brief.py`,
  `seed_translations.py`, `package_release.ps1`, `smoke_test_release.ps1`,
  `write_sha256sums.ps1`, `clang_tidy_sarif.py`, `merge_sarif.py`, `ci_summary.py`).
  `check_translations.py` et `jadg_en.ts` restent : le format du catalogue se décide au LOT-1020.
- **Le numéro de version** : fait, `VERSION.txt` à la racine, lu par le `Build.cs` et par le CMake
  des tests.
- **Les options du jeu** : fait, `Source/Elements/Options/options.json`, lues au lancement.
- **Deux tests de Core à ramener** : `test_dialogue.cpp` (localisation) et le balayage des familles d'entités, écartés parce qu'ils lisent `Source/HMI` ; le reste des tests passe **sans modification de leur code** (critère du LOT-1014). Ils reviennent avec le lecteur de localisation (LOT-1020) et la lecture des entités par le moteur (LOT-1016).
- **Les tests d'automatisation du moteur** : faits, trois tests `Jadg.Socle.*` et une capture
  comparée à tolérance sur une scène sans kit ; `scripts/build.ps1 -Unreal` les enchaîne, sur le
  poste : pas de runner auto-hébergé pour l'instant (D-61).
- **L'empaquetage** : `Source/Elements` est hors de `Content/`, exprès — l'importation automatique
  de l'éditeur surveillerait les images des kits. Les répertoires à embarquer dans une version
  livrée se déclarent au moment du premier paquet.
