# JustAnotherRpgGame

RPG en **C++20** sur **Unreal Engine 5.8** : exploration en temps réel sous une caméra libre, et
rencontres en **combat tactique au tour par tour, en distance**, régi par un système **d20** maison.

> **Fan game non commercial.** Ce jeu gratuit s'inspire des univers de *Dungeons & Dragons* et de
> *Tanares*, sans affiliation ni approbation de leurs ayants droit (Wizards of the Coast, Dragori
> Games). Voir [LICENSE](LICENSE) et [LICENSE-CONTENT](LICENSE-CONTENT).

**Version courante : `0.0.3` — le nouveau moteur**, en cours. Le jeu quitte son moteur maison
(Qt QRhi) pour Unreal Engine 5 ([D-48](Planning/vision/decisions.md), 7 octobre 2026) et change de
dépôt ([D-58](Planning/vision/decisions.md)) : ce dépôt reçoit, par passation, ce que la version
garde — la bibliothèque des règles, les données de contenu, la planification, les scripts. Ce qui
est venu, ce qui est resté et pourquoi : [PASSATION.md](PASSATION.md). Le plan de la version :
[`Planning/versions/v0.1.0/v0.0.3-nouveau-moteur/`](Planning/versions/v0.1.0/v0.0.3-nouveau-moteur/README.md).

## Documentation

Le site du projet est publié à chaque merge sur `main` : **<https://azertval.github.io/JustAnotherRpgGame-UE/>**

| Partie | La question | En ligne | Dans le dépôt |
|---|---|---|---|
| Guide | **Comment** ça marche, et comment s'en servir ? | [Guide](https://azertval.github.io/JustAnotherRpgGame-UE/Guide/index.html) · [Manuel du joueur](https://azertval.github.io/JustAnotherRpgGame-UE/Guide/Manuel/index.html) | [`Documentation/Guide/`](Documentation/Guide/README.md) |
| Spécifications | **Quoi**, et **pourquoi** ? Les exigences `EX-…` | [Spécifications](https://azertval.github.io/JustAnotherRpgGame-UE/Specification/index.html) | [`Documentation/Specification/`](Documentation/Specification/README.md) |
| Cahier de test | Qu'est-ce qui est **vérifié** ? | [Cahier de test](https://azertval.github.io/JustAnotherRpgGame-UE/CahierTest/index.html) | [`Documentation/CahierTest/`](Documentation/CahierTest/README.md) |
| Métiers de Tanares | Quels métiers, quelles populations, et pourquoi ces choix ? | [Étude](https://azertval.github.io/JustAnotherRpgGame-UE/Metiers/index.html) · [Explorateur interactif](https://azertval.github.io/JustAnotherRpgGame-UE/Metiers/explorateur.html) | [`Documentation/Metiers/`](Documentation/Metiers/README.md) |
| Planification | **Quand**, et dans quel ordre ? Versions, lots, décisions | [Planification](https://azertval.github.io/JustAnotherRpgGame-UE/planning/index.html) | [`Planning/`](Planning/README.md) |

Le guide, les spécifications et le cahier de test décrivent encore, pour partie, le moteur maison :
leur relecture est au [LOT-1014](Planning/versions/v0.1.0/v0.0.3-nouveau-moteur/lots/LOT-1014-socle-core-donnees-build.md)
(voir [PASSATION.md](PASSATION.md)). La référence du code (Doxygen) et la page qualité ne sont pas
encore republiées. Contribuer : [CONTRIBUTING.md](CONTRIBUTING.md).

## Les règles de la version

1. **Tout ce qui s'écrit est du texte** ([D-52](Planning/vision/decisions.md)) : C++, JSON de
   contenu, scripts Python d'éditeur, descriptions de carte. Un `.umap` ou un `.uasset` est une
   sortie régénérée par script, en Git LFS. Pas de logique en Blueprint.
2. **`Core` reste la bibliothèque des règles**, sans une ligne du moteur : elle se compile dans le
   module du jeu et, séparément, avec GoogleTest, sans Unreal.
3. **Un lot qui remplace un fichier le supprime** dans sa propre PR (D-32).

## Arborescence

| Dossier | Contenu |
|---|---|
| `JustAnotherRpgGame.uproject`, `Config/` | Le projet du moteur (UE 5.8, module `JustAnotherRpgGame`) |
| `Source/JustAnotherRpgGame/Core/` | Les règles : d20, classes, capacités, sorts, quêtes, dialogues, monde. Inclusions en `"Core/<Module>/<Fichier>.h"` |
| `Source/JustAnotherRpgGame/Bridge/`, `Commandlets/` | Ce que le moteur impose : chemins, journal, le commandlet de contrôle du contenu |
| `Source/ThirdParty/nlohmann/` | nlohmann/json 3.11.3, en-tête unique |
| `Source/Elements/` | Les données de contenu en JSON : `Rpg/`, `World/`, `Levels/`, `Maps/`, `Localization/`. Les kits d'assets s'installent par `scripts/fetch_assets.py` |
| `Source/Elements/Assets/Master/` | Les maillages Meshy **au maître** (D-53) : `manifest.json` est suivi, les `.glb` (2,7 Go) non. `import_master_unreal.py` les importe en Nanite sous `Content/Master/` |
| `Source/Test/Unit/Core/` | Les tests GoogleTest de Core, hors moteur (`CMakeLists.txt` à la racine) |
| `Planning/` | Vision, décisions, versions, lots, standards |
| `Documentation/` | Spécifications, guides, cahier de test (à relire : voir la passation) |
| `scripts/` | Assets, contrôles, documentation, release |

## Construire

```powershell
# Les tests de Core hors du moteur (CMake + Ninja + GoogleTest, environnement MSVC x64 établi par le script)
pwsh scripts/build.ps1

# Le projet Unreal : la cible d'éditeur, puis le contrôle du contenu, sans fenêtre
pwsh scripts/build.ps1 -Unreal
```

Le second enchaîne `Build.bat JustAnotherRpgGameEditor Win64 Development` et
`UnrealEditor-Cmd.exe JustAnotherRpgGame.uproject -run=JadgContentCheck -nullrhi` : le commandlet
lit les catalogues de `Source/Elements/Rpg` par les lecteurs de Core, construit les fiches du
groupe préformé et sort en 1 à la première erreur de contenu.

## Les maillages au maître

Unreal ne borne pas le nombre de triangles d'un maillage : Nanite le découpe lui-même. Les pièces
Meshy se livrent donc **au maître**, sans décimation (D-53). Elles vivent sous
`Source/Elements/Assets/Master/<Famille>/<Référence>.glb` : une pièce porte le nom de sa **référence**
(le dieu de Tanares, la fiche de personnage, la pièce d'équipement), jamais le nom inventé par Meshy.
`references.json` relie chaque retour Meshy à sa référence et dit d'où vient l'attribution ;
`manifest.json` dit, pour chaque pièce, son empreinte, ses triangles et l'asset qu'elle produit.

```powershell
# Ranger un dossier de retours Meshy dans le kit et écrire le manifeste
python scripts/assetsGeneration/build_master_manifest.py D:\Telechargement\Assets

# Importer les pièces du manifeste dans le projet, en Nanite, sans fenêtre
& "<moteur>\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" JustAnotherRpgGame.uproject `
    -run=pythonscript -script="scripts/assetsGeneration/import_master_unreal.py" -unattended -nosplash -nullrhi
```

L'import est rejouable : une pièce déjà présente est laissée telle quelle (`-JadgForce` pour la
refaire), une pièce dont l'empreinte ne correspond plus au manifeste arrête le script.
`-JadgFamily=Weapons`, `-JadgOnly=Statues/Harvest_Fairy`, `-JadgLimit=3` bornent l'import.

Ouvrir `JustAnotherRpgGame.uproject` dans l'éditeur ou générer la solution Visual Studio depuis
le `.uproject` fonctionne comme pour tout projet C++ du moteur.

## Licence

Code sous [PolyForm Noncommercial 1.0.0](LICENSE) ; contenu sous les termes de
[LICENSE-CONTENT](LICENSE-CONTENT) ; bibliothèques tierces dans
[THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
