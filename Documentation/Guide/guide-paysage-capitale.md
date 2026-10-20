# Paysage de la capitale — production par quartier

La livraison est le **paysage de la capitale**, à l'échelle de la métropole de 680 000 habitants : reliefs, terrains des rues et des places, sols, eaux et végétation. **Aucun bâtiment, mur, pont, aqueduc, mobilier ou habitant n'est posé.** Les constructions disposent d'emprises libres ; les franchissements conservent leur lit de rivière ouvert.

La carte assemblée est `/Game/Maps/Levels/capital-landscape/paysage-capitale`. Chaque quartier possède aussi une carte d'inspection `paysage-<quartier>` dans le même dossier. Les sous-niveaux `districts/<quartier>` contiennent seulement le paysage et ses marqueurs d'emprise, sans éclairage supplémentaire. Les cartes de jeu existantes restent indépendantes de cette production.

Pour travailler dans l'éditeur, ouvrir `paysage-capitale`, afficher la fenêtre **World Partition**, puis charger une sélection autour du quartier à retoucher. Le bouton Jouer démarre la caméra près d'Arenarea et charge les cellules voisines. La carte reste un chantier de paysage ; aucun personnage ni parcours de jeu complet n'y est livré.

L'aperçu World Partition se construit par régions de 1 008 m, à une résolution cible de 10 m par pixel. Il sert au repérage dans l'éditeur ; le relief du jeu garde ses échantillons à 4 m. La phase `Minimap` le reconstruit et exporte également `Saved/Jadg/capital-landscape-districts/world-partition/apercu-world-partition.png`.

## 1. Référence et échelle

Le contrat métrique est `Source/Elements/Terrain/capital/atlas.json`, copie avec empreinte SHA-256 de l'atlas du 15 octobre 2026. Les treize quartiers totalisent environ **66,47 km² de terrain urbain**. Le cadre technique, avec baie, collines et abords, couvre **11 088 × 13 104 m**. Il ne prétend pas construire le domaine agricole de 2 500 km² : les 80 000 habitants répartis hors du cadre dans le modèle démographique restent une réserve de monde.

Le nord géographique est **−Y Unreal**, l'est +X et le haut +Z. Le nord placé à droite sur la carte source est bien converti dans ce repère ; ce n'est pas une rotation arbitraire de la géographie. Le zéro vertical correspond au niveau moyen proposé de Tourmaline Bay. Les altitudes de l'atlas restent des cotes de conception, et ne sont pas présentées comme des altitudes canoniques du livre.

Le terrain comporte **143 tuiles de 1 008 m**, chacune avec 252 × 252 quads de 4 m et 16 composants Landscape. Les fichiers sont distribués entre les treize quartiers et un secteur d'abords. Une tuile technique peut traverser une limite administrative : le polygone de quartier reste celui de l'atlas. Les frontières des tuiles ont les mêmes échantillons de hauteur et de peinture ; leurs 262 raccords sont contrôlés bit à bit.

Le chantier détaillé d'Arenarea à 2 m reste dans `/Game/Maps/Levels/capital-landscape/arenarea`. Il fournit la forme du Q07 au terrain commun, avec raccord progressif à ses voisins. Le Landscape commun à 4 m est destiné au relief du site ; les futurs escaliers, bordures et seuils ne sont pas simulés par des marches de quelques centimètres dans cette grille.

## 2. Reliefs et emprises

| Quartier | Relief urbain proposé | Traitement paysager |
|---|---:|---|
| Sloghood | +18 à +56 m | Croupe au-dessus de South Creek, petits replats domestiques et végétation clairsemée |
| Uptown | +46 à +68 m | Pentes douces, terrasses de jardin et arbres d'ombrage |
| Artisansquare | +42 à +62 m | Plateau de travail, cours horizontales réservées, poches végétales |
| Scholarnest | +26 à +58 m | Éperon académique et plateformes de parvis |
| Dweomer | +26 à +48 m | Croupe vallonnée, grands jardins, plateformes séparées |
| Martpart | +18 à +26 m | Terrasse marchande basse, terrains des accès de livraison |
| Arenarea | +14 à +28 m | Terrasses patriciennes, trois jardins et bassin littoral bas |
| Oldtown | +10 à +38 m | Rive historique, plateaux industriels et montée vers le cimetière |
| Neckoffoods | +24 à +46 m | Champs de 180 × 360 m, tournières en terre et arbres de bordure |
| Bloomburgs | +38 à +60 m | Replats de faubourg et petites poches de jardin |
| Downtown | +26 à +50 m | Dos de terrain civique et réservations des places |
| Palacedomain | +44 à +78 m | Promontoire et jardins boisés, plateformes du palais conservées |
| Docks District | +3 à +8 m | Sols bas des quais et des cours portuaires |

Ces bandes décrivent les secteurs urbains, hors fonds de rivière, rives basses et marges de raccord. Les statistiques d'une tuile ne doivent donc pas être prises pour les altitudes d'un quartier entier. Les collines occidentales atteignent environ +240 m. Les terrasses sont modelées en terre ; aucun mur de soutènement n'est implicitement ajouté.

Deux raccords demandent une lecture particulière : le terrain de Martpart remonte vers le musée de Scholarnest, jusqu'à +48,48 m sur la frontière, et la bordure des docks monte vers Arenarea, jusqu'à +21,93 m. Ce sont des talus de liaison, pas les cotes des cours marchandes ou des quais. À plus de 220 m des limites et des berges, les échantillons contrôlés restent entre +18,62 et +26 m à Martpart, et entre +4,50 et +7,87 m aux docks.

Les parcelles des lieux repères sont aplanies à leur cote, avec une transition de terrassement autour. Les jardins botaniques et les terres des Crops restent des paysages : leurs grandes emprises ne deviennent pas de faux socles de bâtiments. Les cavernes sous le palais ne sont pas converties en une dépression de surface. Le sanctuaire dont l'entrée n'est pas localisée reste sans implantation inventée.

L'Arena of Fate conserve sa dimension de projet **189 × 156 × 48 m**. Seul son terrain est préparé ; son modèle n'est ni posé ni redimensionné. Les marqueurs `04_Emprises_libres` sont réservés à l'éditeur et ne produisent aucun volume visible dans le jeu.

## 3. Sols, eaux et végétation

Sept couches de terrain restent accessibles : **Pelouse, Prairie, HerbeSauvage, Terre, Sable, Roche et Pavage**. Les trois herbes utilisent les nouvelles surfaces Fab ; les autres réemploient les cartes PBR fournies dans le projet. La couche Pavage indique une surface minérale et des réservations de sol. Les pavés construits, bordures et mobiliers appartiendront à une autre commande.

Les couches partagent leurs poids entre couleur, normales et rugosité. Leur mélange est normalisé dans le matériau. Les copies de travail portent leur provenance ; aucune carte de relief n'est inventée à partir d'une couleur. La préparation des couches Landscape est finalisée avec le rendu actif avant sauvegarde.

La matière métropolitaine réemploie les cartes PBR avec un mélange de trois décalages sur un réseau triangulaire pour les sept sols. Les décalages changent à l'échelle d'une répétition de texture pour limiter les motifs réguliers visibles dans les vues éloignées. Couleur, normale et rugosité gardent les mêmes coordonnées ; les dérivées originales évitent des coutures de mipmaps. Les textures sources et leur échelle ne changent pas.

La baie, la Rubicund, South Creek et le bassin d'Arenarea ont des surfaces d'eau distinctes du terrain. Les niveaux suivent l'atlas ; les deux cours d'eau continuent au-delà du bord de la carte, et la baie reste ouverte au sud. Les tracés de futurs ponts ne bouchent pas les chenaux. L'eau utilise le matériau Single Layer Water du projet, sans collision de sol.

Les herbacées proviennent de quatre familles Fab, en 27 variantes : Ribbon Grass, Wheat Grass et les deux familles Wild Grass. Les cyprès et arbres d'ombrage déjà présents dans le projet complètent les jardins et boisements ; ils ne sont pas présentés comme de nouveaux assets Fab. Les maîtres sont conservés. Les plantations utilisent des FoliageTypes natifs et des ressources Nanite, avec une graine déterministe.

Le placement exclut les emprises bâties, les routes, les sols immergés et les pentes trop fortes. Les arbres des champs se concentrent sur les bordures ; les herbes de berge suivent les eaux. Les matières des plantes sont copiées et compilées pour Nanite et l'instanciation. La densité reste une décision paysagère par quartier ; aucune optimisation globale de la ville n'est revendiquée.

Une vérification repère les cellules dont la courbure peut éloigner une plantation du triangle réellement rendu. Ces racines sont reprojetées sur la collision native de leur composant Landscape, avec un enfouissement de 1 cm, puis contrôlées après réouverture. Le relief lui-même ne change pas lors de cette correction.

## 4. Phases et contrôles

L'ordre de production commence par Arenarea, Martpart et Oldtown, puis les docks, le centre civique, le domaine du palais, Uptown, Artisansquare, Scholarnest, Dweomer, Sloghood, Bloomburgs, Neckoffoods et enfin les abords. Chaque secteur passe successivement par :

1. Import du relief, de la peinture et des eaux ; sauvegarde du niveau.
2. Application des matières et construction des ressources Nanite ; sauvegarde.
3. Plantation native, sans bâtiment ; sauvegarde.
4. Réouverture, contrôle des collisions, des poids de peinture, des ressources Nanite et du nombre de plantes ; captures à midi et à 22 h.

Les rapports résident sous `Saved/Jadg/capital-landscape-districts/<Qxx>`. Les images se trouvent sous `Saved/Captures/capital-landscape-districts/<quartier>`. Le plan général `Saved/Jadg/capital-landscape-districts/plan-capitale.png` représente les données réellement importées, et non une illustration d'intention.

La vérification de paysage ne certifie pas une navigation de jeu complète. Les bâtiments, ponts, réseaux de circulation finale, intérieurs et quêtes sont absents de cette passe. Les cadrages d'inspection utilisent les limites de la caméra du joueur ; l'assemblage complet sert également de base de travail dans l'éditeur.

## 5. Reproduction

Fermer les autres instances Unreal utilisant le projet. Compiler le module d'éditeur pour disposer de l'import du Landscape et de la plantation native. Depuis le dossier du projet :

```powershell
pwsh scripts/maps/review_capital_landscape_districts.ps1 -Phase All
```

`-Districts Q06` limite la production à Martpart. `-SkipPrepare` réutilise les données préparées. `-Resume` conserve les secteurs déjà audités ; il s'emploie uniquement si les données et producteurs sont inchangés. `-Phase Capture` reprend les images ; `-Phase Assemble` recompose la carte globale depuis les sous-niveaux audités.

Sur ce poste, le disque C: était saturé pendant la production. Les fichiers temporaires et le cache de construction sont dirigés vers E:. Le paramètre `-ZenPort 8559` permet de se connecter au serveur de cache déjà démarré sur E: ; l'omettre utilise le lancement habituel d'Unreal. `-nowrite` empêche les écritures de préférences globales, sans empêcher les sauvegardes des cartes et assets.

Producteurs : `prepare_capital_landscape_districts.py`, `build_capital_landscape_water.py`, `build_capital_landscape_districts.py`, `capital_foliage_materials.py` et `review_capital_landscape_districts.ps1`. Le contrat de production est `Source/Elements/Terrain/capital/production.json`. Les sources et identifiants Fab sont consignés dans `Source/Elements/Assets/Library/arenarea-fab-sources.json`.

## 6. World Partition et recette de chargement

La carte livrée doit utiliser World Partition avec streaming activé. Les cartes `paysage-<quartier>` restent des ateliers d'inspection indépendants. `construction-capitale` est l'assemblage intermédiaire qui sert uniquement à produire le monde partitionné final.

Le réglage de départ utilise des cellules de **504 m**, un rayon de chargement de **1 512 m** et des groupes de végétation de **252 m**. Ces tailles correspondent aux composants de 63 quads à 4 m. Les HLOD lointains sont répartis en cellules de **1 008 m**, avec une portée de **6 048 m**, pour construire chaque représentation par secteur. Le blocage global sur un streaming lent est désactivé ; la recette mesure les délais réels. Les proxies Landscape et les acteurs de végétation doivent être spatialement chargés. L'éclairage et les points de cadrage restent globaux.

La conversion comporte d'abord une fusion intermédiaire en One File Per Actor, puis le passage en World Partition. Cela évite le défaut documenté [UE-353028](https://issues.unrealengine.com/issue/UE-353028) lors d'une conversion directe de Landscapes situés dans des sous-niveaux. Les ateliers sources sont conservés. Les représentations Nanite sont reconstruites après partitionnement, puis les HLOD produisent les silhouettes lointaines. Les herbes restent un détail local ; les arbres participent aux vues lointaines.

Le commandlet `JadgConvertCapital` appelle le convertisseur standard après avoir rétabli les pointeurs temporaires des attaches de végétation depuis leurs références sauvegardées. Cela contourne le déréférencement d'une attache nulle rencontré dans le convertisseur de végétation de 5.8.3, sans modifier les sources d'Unreal ni les transformations des plantations.

```powershell
pwsh scripts/maps/review_capital_landscape_districts.ps1 -Phase Assemble
pwsh scripts/maps/review_capital_world_partition.ps1 -Phase All
```

`Source/Elements/Terrain/capital/world-partition.ini` conserve les réglages de conversion. Les étapes `Convert`, `Configure`, `HLOD`, `Audit`, `Capture`, `Streaming` et `Minimap` peuvent être reprises séparément ; `Partition` reprend la conversion depuis la fusion intermédiaire et `Finalize` duplique un monde déjà converti vers la carte finale. `configure_capital_world_partition.py` contrôle les acteurs externes, les hauteurs, la peinture du terrain et le nombre d'instances conservées après conversion.

La recette utilise une arrivée dans chaque quartier, puis un déplacement continu de 1 280 m à 16 m/s. Elle enregistre le délai jusqu'au terrain chargé, les images par seconde, le 99e centile, la pire trame et le nombre de proxies chargés. Les captures attendent aussi la fin du streaming. La présence de World Partition ne vaut pas, à elle seule, validation de la cible de fluidité.

Références Epic : [World Partition](https://dev.epicgames.com/documentation/en-us/unreal-engine/world-partition-in-unreal-engine), [outils de construction](https://dev.epicgames.com/documentation/unreal-engine/world-partition-builder-commandlet-reference?lang=en-US) et [HLOD](https://dev.epicgames.com/documentation/en-us/unreal-engine/world-partition---hierarchical-level-of-detail-in-unreal-engine). Le comportement des outils a également été vérifié dans les sources locales d'Unreal 5.8.3.

## 7. Résultats mesurés le 16 octobre 2026

Le paysage des treize quartiers et des abords est construit. La carte finale utilise World Partition, ses données Nanite sont à jour, et les 28 vues à midi et à 22 h ont été examinées. Les ateliers par quartier restent disponibles.

| Contrôle | Résultat |
|---|---:|
| Portions de terrain chargées spatialement | 572 sur 572 |
| Composants Landscape conservés | 2 288 |
| Végétation conservée après conversion | 3 337 068 instances |
| Groupes de végétation chargés spatialement | 2 117 sur 2 117 |
| Raccords de données entre tuiles | 262, identiques en hauteur et en peinture |
| Contrôles natifs après conversion | 572 points, aucune erreur |
| Écart numérique maximal sur la hauteur contrôlée | 0,8 mm |
| Écart maximal de peinture, sur une échelle 0–1 | moins de 0,00000003 |
| Géométrie Nanite du terrain complet | 18 743 296 triangles sources |
| Acteurs HLOD construits | 766, tous avec une représentation |
| Portions de terrain couvertes par les HLOD | 572 |
| Bâtiments ou autres maillages statiques inattendus | 0 |

L'écart de 0,8 mm concerne la comparaison numérique des échantillons contrôlés ; ce n'est pas une résolution millimétrique du relief. La grille du terrain reste à 4 m. Les 44 acteurs de maillage statique autorisés sont les surfaces d'eau. Les 143 acteurs Landscape d'origine ne portent plus de géométrie rendue : celle-ci réside dans les proxies partitionnés.

La recette a tourné en **1920 × 1080**, avec **Lumen et Nanite actifs**, sur l'i7-8700 et la RTX 4060 Ti 8 Go du poste, avec 16 Go de RAM. Il s'agit du mode jeu de l'éditeur, avec caches déjà utilisés pendant la construction ; ce n'est pas une mesure d'une distribution cuite sur un autre ordinateur.

| Mesure | Résultat |
|---|---:|
| Moyennes des 14 arrêts, après arrivée du terrain | 64,5 à 93,4 images/s |
| Secteur le plus coûteux | abords boisés, 64,5 images/s |
| Terrain chargé à ces arrêts | 36 à 60 proxies sur 572 |
| Attente du terrain après téléportation | 0,51 à 5,16 s |
| Déplacement continu | 1 280 m à 16 m/s, environ 80 s |
| Moyenne pendant ce déplacement | 85,95 images/s |
| 99e centile du temps d'image pendant ce déplacement | 25,81 ms |
| Pire image pendant ce déplacement | 57,35 ms |
| Contrôles de sol pendant ce déplacement | 390, aucun sol manquant |
| Mémoire du processus à la fin du parcours | environ 4,36 Gio |
| Mémoire GPU relevée pendant les captures | environ 4,51 Gio |

**La cible de 60 images/s est dépassée en moyenne dans les secteurs mesurés ; une cadence constante à 60 images/s n'est pas garantie.** Des pointes dépassent le budget de 16,67 ms, y compris pendant le déplacement continu. Les arrivées par téléportation produisent des images allant jusqu'à 185,53 ms. Les résultats justifient le streaming et la continuité du terrain, pas une absence totale de saccades. Les abords et les transitions constituent les prochains secteurs à profiler si une contrainte stricte de temps d'image est retenue ; aucune baisse globale de densité ou de qualité n'a été appliquée pour embellir les chiffres.

Les sources de mesure sont `Saved/Jadg/capital-landscape-districts/world-partition/audit.json`, `streaming-performance.json` et `Saved/Captures/capital-world-partition/mesure.json`. Les planches `revue-1200.jpg` et `revue-2200.jpg` rassemblent les vues natives du monde final. Le rendu laisse encore percevoir des répétitions de texture dans les grands aplats réservés ; les couches restent éditables pour une passe artistique locale.

La compilation d'éditeur et les contrôles des descriptions de carte passent. Le contrôle des fichiers non référencés ne signale plus de sortie de ce chantier ; il conserve le signalement préexistant de `Content/Maps/Levels/essai/NewWorld.umap`, que cette production ne supprime pas.

Le nettoyage du disque C: a retiré 468 fichiers de cache graphique déverrouillés, soit environ **30,4 Go**. Les fichiers personnels et téléchargements Fab ont été conservés ; les caches et temporaires de cette construction sont dirigés vers E:.
