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
  dépôt et va en Git LFS ; `check_orphans.py` cite chaque sortie par le script qui la produit. **Pas
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
`pwsh scripts/build.ps1 -Unreal` (cible d'éditeur, puis commandlet `JadgContentCheck`).

## Lots d'assets 3D

Les maillages se livrent **au maître** : Unreal ne borne pas le nombre de triangles (Nanite), ni
décimation ni budget de triangles. Les retours Meshy vont dans `Source/Elements/Assets/Master/` par
`build_master_manifest.py`, et dans le projet par `import_master_unreal.py` ; jamais par un import
à la main dans l'éditeur.

Avant de produire ou retoucher un lot d'assets, lire `Planning/standards/style-3d.md` — notamment
« Critères de qualité validés par l'auteur » et « Ce qui reste ouvert » — et, pour un personnage,
`Planning/standards/personnages-3d.md`. Ses valeurs de géométrie (§1), de poids (§3) et d'images
tolérées (§7) sont périmées par D-49 et D-53 et se réécrivent au `LOT-1019`.

Un personnage est un maillage qui lui est propre, généré par Meshy depuis une vue de face en pose
neutre (de trois quarts pour un quadrupède), puis lié au squelette commun de sa silhouette par
script ; il s'importe **au maître**, sans décimation (D-53). Aucune retouche à la main d'un
maillage ni d'une texture : la chaîne se rejoue, ou la pièce se recommande. Les articulations et les
clips se règlent dans Blender par l'atelier des assets (D-44) : ce qui en revient est une donnée que
la chaîne rejoue, jamais un maillage exporté par Blender.

Le standard n'écrit que des valeurs mesurées ou des décisions datées de l'auteur. Ne pas combler une
question ouverte par une valeur devinée : la poser à l'auteur, ou la laisser au lot que le standard
nomme.
