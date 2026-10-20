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
`build_master_manifest.py`, et dans le projet par `import_scenery_unreal.py` (LOT-1019 : une pièce
entre depuis sa fiche, avec sa matière complète et ses textures compressées par le moteur) ; jamais
par un import à la main dans l'éditeur.

Avant de produire ou retoucher un lot d'assets, lire `Planning/standards/style-3d.md` — réécrit au
`LOT-1019` sur les mesures du moteur —, notamment « Critères de qualité validés par l'auteur » et
« Ce qui reste ouvert » ; le gabarit de commande d'une zone (`gabarit-commande-zone.md`) demande
des pièces au maître, toutes faces finies. `Planning/standards/personnages-3d.md` a été réécrit au
`LOT-1015` sur les mesures du moteur (D-63, D-64) : c'est lui qui vaut pour un personnage.

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

## Base de construction de la capitale — décision utilisateur du 16 octobre 2026

La carte active est `/Game/Capitale/Cartes/Capitale`. Elle remplace `paysage-capitale` ; les anciennes cartes `paysage-*`, les montages de quartiers et les essais redondants sont archivés hors Content. Ne pas les recréer automatiquement. Le terrain, ses couches peintes, les rues et les ressources validées sont conservés ; le feuillage placé a été supprimé à la demande de l’utilisateur.

Content est organisé en `Capitale` (carte et ressources du terrain), `Atelier` (trois galeries), `Bibliotheque` (assets et matériaux réutilisables), `Jeu` (dépendances de jeu). Les dossiers `__ExternalActors__` et `__ExternalObjects__` appartiennent à World Partition et ne doivent pas être déplacés dans l’Explorateur.

Les galeries actives sont `GalerieAssets`, `GalerieMateriaux` et `PhysiqueTissus`, dans `/Game/Atelier/Cartes`. Les anciens générateurs de cartes sont des sources historiques protégées contre une relance directe. Les corrections manuelles guidées dans Unreal sont autorisées par la demande utilisateur actuelle. Les anciens scénarios de gameplay dépendant des cartes archivées ne font pas partie de cette base de construction.


## Relief naturel de la capitale — validation utilisateur du 16 octobre 2026

La géographie suit `capitale-vue-ensemble-v04.png` ; le catalogue topographique fournit seulement les références de hauteurs (pages 9-12). La prévisualisation v02 a été acceptée. Le Landscape a été reconstruit depuis `Source/Elements/Terrain/capital/relief-reference` : 4,032 km de côté, pas de 2 m. Cette décision remplace la conservation antérieure des rues et des emprises : la carte active ne contient que le relief, l’eau et les acteurs techniques du ciel et de contrôle. Aucune rue, plateforme de bâtiment, construction ou végétation placée ne doit être réintroduite automatiquement. Construire Nanite successivement, pas en masse sur ce poste de 16 Go.

Révision du 17 octobre 2026 (rivages et reliefs précis, à juger par l’auteur) : le rivage n’est plus tracé à main levée, il est **lu sur la vue v04** (couleur de l’eau) et projeté au sol par une caméra à 60° décrite dans `relief-reference/geographie.json` ; ce fichier texte porte aussi les axes de la rivière et du ruisseau, les repères d’altitude (valeurs du catalogue inchangées, repositionnées sur l’image) et les zones. `controle-rivage.png` montre la vue redressée et le rivage obtenu. Le matériau actif est `ReliefReference/MI_TerrainNaturel`, instance de `M_TerrainNaturel` (`build_capitale_terrain_material.py`) : fondu de distance à trame tournée, macro-variations, roche triplanaire automatique, mélange par hauteur, berges humides, déplacement Nanite et sortie vers `RVT_TerrainNaturel` (pas encore affecté aux Landscape : avec lui, l’éditeur 5.8 plante au chargement avec rendu). La finalisation Nanite tourne sans rendu (`-nullrhi`). Chaque Landscape a deux couches d’édition : `Relief_Reference` (générée) et `Retouches` (à la main). `scripts/maps/rebuild_capitale_relief.ps1` rejoue toute la chaîne ; son étape « retrait » exige une sauvegarde vérifiée de la carte remplacée.

Révision du 17 octobre 2026, demande de l’auteur (à juger par lui) : la référence n’est plus la vue v04 mais le **Guide de Création** (`references-capitale/output/Guide de Creation.pdf`), lu planche par planche dans le PDF (`scripts/maps/guide_capitale.py`). Le relief suit les **courbes de niveau de la planche 06** (`relief_guide.py` : squelette des courbes, interruptions raccordées, crans des bandes par moindres carrés — une boucle fermée monte —, surface la plus douce entre les courbes) ; le guide ne chiffre rien, l’équidistance et le niveau viennent des repères du catalogue (≈ 7,3 m par courbe). La planche est posée à plat, 2,7024 m par pixel, sur toute la largeur du Landscape ; 784 m de collines la prolongent au nord, 400 m au sud. Le **réseau routier de la planche 04** est réintroduit à la demande de l’auteur, peint sur le Landscape : pavé (`Pavage`) dans l’enceinte relevée sur la planche 01, terre battue (`Chemin`) au-dehors ; largeurs par classe (ruelle 4,5 m, rue 7 m, avenue 12 m), le dessin donnant 16 à 32 m à cette échelle. Le couvert vient de la planche 02 (`Foret`, prairies, terre sèche). Le Natural Pool de l’ancienne vue est la Petite Anse du guide, ouverte sur la baie. Neuf couches peintes ; déplacement Nanite (tessellation) sur toutes, lu sur leurs cartes de hauteur. Le streaming World Partition est actif (`configure_capitale_streaming.py` : cellules de 504 m chargées à 1,6 km, HLOD au-delà — relief pris à la LOD 2, jamais à la plus grossière, dont la jupe Nanite de 63 m creusait le bord de la vue d'ensemble —, l’eau toujours chargée, construits par `WorldPartitionHLODsBuilder`). Toujours ni bâtiment, ni pont, ni rempart, ni végétation placée.

Révision du 18 octobre 2026, demande de l'auteur (à juger par lui) : deux exceptions à la phrase précédente. **Les forêts hors les murs** : un graphe PCG (`build_capitale_vegetation.py`, partitionné en cellules de 256 m, rangées ensuite dans la partition de streaming `Vegetation`, chargée à 4,5 km et sans HLOD : le HLOD fusionné de la forêt dépasse les 16 Go du poste), décrit par `Source/Elements/Terrain/capital/vegetation.json` — cinq strates (arbres, gaulis, sous-bois, rochers, bosquets) des packs Fab `CommonHazel` et Megascans, posées là où la couche `Foret` (ou `HerbeSauvage` pour les bosquets) l'emporte, l'enceinte de la planche 01 retirée par une spline fermée tracée dans le graphe ; générées par `PCGWorldPartitionBuilder`. Les herbes des prairies poussent par un Landscape Grass Type branché sur `M_TerrainNaturel`, jamais sauvegardées. Rien de végétal n'est placé dans l'enceinte. **L'Arena of Fate** : le monument du LOT-1022 (`Levels/.../arena-of-fate.json`, sept étages, sous-sols compris, car les portes du grand axe y descendent) posé par `place_capitale_arena.py` à son emprise, lue sur la planche 01 (`geographie.json`, clé `arene`) ; le relief y est mis de niveau à la médiane de l'emprise, parvis pavé, et creusé sous l'ovale. Le Landscape reste un Landscape (Mesh Terrain écarté par l'auteur le 17 octobre). Les deux étapes `vegetation` et `arene` de `rebuild_capitale_relief.ps1` précèdent les HLOD.

Révision du 19 octobre 2026, demande de l'auteur (à juger par lui) : **la végétation est retirée** — la première exception ci-dessus ne vaut plus. Ni forêt PCG, ni herbe de Landscape : `retire_capitale_vegetation.py` (étape `sans-vegetation`, à la place de `vegetation`) retire le volume PCG, ses acteurs de partition, le type d'herbe et ses références en cache dans les composants du Landscape (`UJadgSceneBuild::RefreshLandscapeGrass`) ; `M_TerrainNaturel` n'a plus de sortie d'herbe. Les packs Fab restent au projet sans être posés. **L'Arena of Fate est reprise sur le Colisée** (la planche validée `arena-of-fate-planche-v1.png` et le référentiel de la capitale) : sable en contrebas d'un podium de 3 m plaqué de marbre, coursive des quatorze dieux avec un brasero entre deux statues, portes du triomphe et des morts sous le podium sur le grand axe ; cavea continue en trois maeniana séparés par des baltei percés de vomitoires, loges des treize délégations encastrées dans la media cavea, haut mur et portique couvert au sommet, velum sur mâts ; aucune tour d'escalier visible, les passages des portes courent sous les gradins (`scripts/assetsGeneration/arena_cavea.py`). Les garnitures viennent du catalogue unitaire de l'arène (`aof-catalogue.json`, assets `/Game/Bibliotheque/ArenaFate`), posées par leur asset du projet. L'arène a sa partition de streaming `Arene` (chargée à 4,5 km, sans HLOD : le HLOD fusionné de sa cellule fait planter le processeur graphique du poste). Les gradins sont desservis à la romaine, sans escalier visible depuis l'arène : chaque vomitoire des deux baltei est un passage réel creusé sous les gradins jusqu'aux déambulatoires de 12 et 24 m (portes au pied du haut mur), et quatre cages d'escalier sur les diagonales, creusées dans la masse et ouvertes seulement sur les déambulatoires (escalier en U du sol à 12 m, volée de 12 à 24 m), relient le parvis aux deux praecinctiones ; les loges se gagnent par l'arrière de leur encoche. `verify_capitale_arena_access.py` (étape `controle`) le vérifie sur le maillage de navigation, au profil fin de l'arène (tuiles de 3 m, douze couches) ; les catacombes, ouvertes par un mur à interrupteur caché, y comptent comme fermées. La collision des gradins et des escaliers se prend sur un repli Nanite complet (`preserve_walkable_collision`) : le repli simplifié effaçait les marches.

Seconde révision du 19 octobre 2026, demande de l'auteur (à juger par lui) : **la démo est réintroduite, simplifiée, autour de l'arène**, sans autre zone (« le colisée est suffisamment imposant »). `scripts/maps/capitale_demo.py` (étape `demo`, après `arene`) écrit la carte de Core `Source/Elements/Levels/Capitale.json` — la grille de l'arène prolongée jusqu'au parvis sud, ses sept étages, la zone de combat, les rencontres de la série et les points d'entrée du groupe recopiés d'`arena-of-fate.json` — et pose dans la carte la mère à son étal devant la porte du sud (le groupe arrive face à elle), le garde devant les cellules de la prison avec l'enfant dedans, et le maître d'arène à la porte du triomphe, au bord du sable, qui lance les combats. La quête des pommes et ses dialogues sont inchangés. La capitale est sa propre carte d'arène (`ArenaMap`) : le combat se joue sur son sable. Le groupe, les personnages, le repère de la carte de Core (au coin de la grille, au sol de l'arène), la navigation de l'arène et son contrôleur (profil fin, coupe de caméra) sont toujours chargés. Chaque loge a deux porte-bannières de sa délégation. Révision du 20 octobre 2026 : vestiaires et prison sont aménagés en lieux détaillés par `scripts/assetsGeneration/arena_undercroft.py` (loculi, armurerie, tables de massage, fosse d'entraînement ; quatre cellules grillagées dont celle de l'enfant fermée, enclos des condamnés, poste du garde, pilori), complétés par les meubles du catalogue ; la navigation de l'arène est construite avec la carte (Static, morceaux World Partition de `WorldPartitionNavigationDataBuilder`, étape `navigation`), pour l'agent du jeu déclaré dans `Config/DefaultEngine.ini` (1,90 m, rayon 25 cm : la capsule des personnages) ; un écran de chargement (`UI/JadgLoadingScreen`, illustrations de `Source/Elements/Assets/UI/loading.json`) couvre le chargement de la carte et la mise en place du monde.
