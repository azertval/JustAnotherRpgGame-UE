# Consignes persistantes du projet

## Le nouveau moteur (décision D-48, 7 octobre 2026)

Ce dépôt est celui du **nouveau moteur** : Unreal Engine 5.8, version `0.0.3`,
`Planning/versions/v0.1.0/v0.0.3-nouveau-moteur/`, lots `LOT-1012` à `LOT-1023`. Il a reçu par
passation ce que la version garde ; ce qui est venu et ce qui est resté est dans `PASSATION.md`.
**Rien de Qt, de QML ni de QRhi n'y entre** (D-58) : l'ancien dépôt reste la référence du moteur
maison, en privé, jusqu'à la recette (`LOT-1023`).

Règles de la version :

- **Tout ce qui s'écrit est du texte** (D-52) : C++, JSON de contenu, scripts Python d'éditeur,
  descriptions de carte. Tout ce qui est binaire (`.umap`, `.uasset`) se régénère par un script du
  dépôt et reste sur le poste (`Content/` n'est pas suivi, D-60) ; `check_orphans.py` cite chaque sortie par le script qui la produit. **Pas
  de logique en Blueprint.**
- **`Source/JustAnotherRpgGame/Core` est la bibliothèque des règles, sans dépendance au moteur.**
  Elle se compile dans le module du jeu et, à part, avec GoogleTest (`CMakeLists.txt` racine). Une
  règle que le moteur impose à Core s'écrit dans Core et vaut pour les deux constructions. Ses
  inclusions sont `"Core/<Module>/<Fichier>.h"`, jamais un nom seul.
- **Core avant le moteur** dans l'ordre des inclusions d'un fichier du jeu : les en-têtes de Core ne
  doivent voir aucune macro d'Unreal (`check`, `verify`, `ensure`). `Core/Combat/BattleGrid.h`
  déclare une méthode `check(...)` et ne se consomme pas depuis le moteur ; il disparaît au LOT-1017.
- Les données de contenu restent en JSON sous `Source/Elements/`, lues par les lecteurs de Core
  (nlohmann) ; aucune `DataTable` ni `.uasset` de données. Un lecteur Unreal ne s'écrit que là où
  le moteur l'impose (textures, maillages, sons), et il est régénérable.
- Chaque lot qui change l'image livre ses captures, à midi et à 22 h, au cadrage du joueur.
- Un lot qui remplace un asset, un script ou un document le supprime dans sa propre PR (D-32).

Construire et vérifier sans fenêtre : `pwsh scripts/build.ps1` (tests de Core) et
`pwsh scripts/build.ps1 -Unreal` (cible d'éditeur, commandlet `JadgContentCheck`, tests
d'automatisation `Jadg.*`, puis carte du socle et captures comparées à leur référence ;
`-NoCapture` sans processeur graphique) ; `-Unreal -Parcours` joue la quête des pommes dans le jeu
lancé, sur les deux cartes d'essai de l'exploration (LOT-1016). Un test du moteur s'écrit sous
`Source/JustAnotherRpgGame/Tests/`, son nom commence par `Jadg.` ; une règle se teste d'abord hors
du moteur (`Source/Test/Unit/Core`).

## Lots d'assets 3D

Les maillages se livrent **au maître** : Unreal ne borne pas le nombre de triangles (Nanite), ni
décimation ni budget de triangles. Les retours Meshy vont dans `Source/Elements/Assets/Master/` par
`build_master_manifest.py`, et dans le projet par `import_master_unreal.py` ; jamais par un import
à la main dans l'éditeur.

Avant de produire ou retoucher un lot d'assets, lire `Planning/standards/style-3d.md` — notamment
« Critères de qualité validés par l'auteur » et « Ce qui reste ouvert ». Ses valeurs de géométrie
(§1), de poids (§3) et d'images tolérées (§7) sont périmées par D-49 et D-53 et se réécrivent au
`LOT-1019`. `Planning/standards/personnages-3d.md` est **périmé** par D-63 et D-64 jusqu'au
`LOT-1015`, qui le réécrit sur les mesures du moteur : seuls son §3 (l'image de référence, pour les
pièces Meshy) et son §10 (portrait et jeton peints) valent encore.

Un personnage est une **fiche texte** (JSON) qui donne les valeurs des paramètres d'un **objet
personnalisable Mutable** ; le créateur assemble corps, tête, pièces, garde-robe et matières (D-63).
Les corps et têtes humains et proches de l'humain viennent de **MetaHuman** ; ce que MetaHuman
n'atteint pas, et les pièces propres au monde (cornes, défenses, queues, oreilles, armures
signatures, armes), viennent de **Meshy**, ou de **Fab** pour les corps de base, la garde-robe et
les animations. Tout est sur le squelette standard d'Unreal, les animations viennent des
bibliothèques du moteur reciblées par l'IK Retargeter, les armes s'accrochent par socket. Le
créateur se régénère par script depuis sa description texte ; aucun asset construit à la main dans
l'éditeur ne reste, et aucune retouche à la main d'un maillage ni d'une texture : la pièce se
recommande. La chaîne maison (squelettes MPFB et `quadruped`, clips posés par cibles, retouche dans
Blender) ne se porte pas : elle se supprime (D-64). Portraits et jetons restent peints (D-30).

Le standard n'écrit que des valeurs mesurées ou des décisions datées de l'auteur. Ne pas combler une
question ouverte par une valeur devinée : la poser à l'auteur, ou la laisser au lot que le standard
nomme.
