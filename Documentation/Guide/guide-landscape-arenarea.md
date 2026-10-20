# Arenarea — premier quartier du Landscape

Cette livraison traite uniquement Arenarea. Elle reprend le quartier Q07 du catalogue topographique du 15 octobre 2026, à l'échelle de la métropole de 680 000 habitants. Arenarea couvre **6,127 km²** et réserve l'espace de ses 45 000 habitants. Les constructions, intérieurs et habitants feront l'objet de passes ultérieures ; la carte contient aujourd'hui leur terrain et les réservations des lieux repères.

Ouvrir **`/Game/Maps/Levels/capital-landscape/arenarea`** dans Unreal. Le fichier est `Content/Maps/Levels/capital-landscape/arenarea.umap`. La carte de jeu existante `central-empire/capital/arenarea` conserve ses quêtes et son implantation antérieure.

## 1. Relief

Les hauteurs, limites et réservations proviennent de `Source/Elements/Terrain/arenarea/definition.json`, copie ciblée et référencée des données de l'atlas. Le nord géographique est **−Y Unreal**, l'est +X ; le nord placé à droite sur la carte du livre est ainsi correctement interprété. Le zéro vertical est le niveau moyen proposé de Tourmaline Bay.

Le terrain technique couvre **3 024 × 4 284 m**, dont une marge rectangulaire pour raccorder plus tard les voisins. Son pas est de **2 m**, avec 1 512 × 2 142 quads répartis en 816 composants. La limite Q07 est visible sur le plan de contrôle ; la marge ne signifie pas que les quartiers voisins sont conçus.

Le quartier urbain suit les terrasses de +14 à +28 m. Les plateformes principales sont l'Arena et Dusk of Justice à +20 m, le casino et l'hippodrome à +23 m, le bazaar à +24 m. Trois jardins sont aménagés à +17, +23 et +26 m. Le bassin littoral est une exception : eau +0,20 m et fond −3 m. La rivière descend vers la baie selon les niveaux de l'atlas. Le chenal du bassin est prolongé jusqu'à la baie pour fermer un écart d'environ 100 m entre les deux tracés sources.

L'arène existante reste **189 × 156 × 48 m**. L'atlas proposait une autre cote ; cette passe ne redimensionne aucun bâtiment. Elle réserve la parcelle de 450 × 540 m et son plateau. Les marqueurs dans `01_Relief/Reservations` identifient les six lieux ; ce ne sont pas leurs modèles définitifs.

Les accès principaux font 24 m ; les liaisons locales vers les lieux font 15 m et les allées de jardin 6 m. Les liaisons ajoutées sont explicitement des décisions de conception locales dans le rapport de relief. Les profils et plateformes sont préparés avant les matières.

L'approche sud d'Herofate est localement déviée vers l'est avant le bazaar, puis traverse son espace public à +24 m. Le segment droit de l'atlas traversait cette plateforme à une cote plus basse. Les nœuds originaux restent conservés dans la définition. Le contrôle échantillonné tous les 2 m mesure au maximum 5,60 % sur Herofate, 4,30 % sur l'accès de l'arène et 7,42 % sur l'allée du jardin bas ; il rejette un accès dépassant 8 %.

## 2. Matériaux

`/Game/CapitalLandscape/Arenarea/Materials/MI_Surfaces` propose sept couches peintes : **Pelouse, Prairie, HerbeSauvage, Terre, Sable, Roche, Pavage**. Couleur, normales et rugosité utilisent les mêmes poids. Les trois premières utilisent les nouvelles surfaces Fab : Lawn Grass `tkynejer`, Uncut Grass `oilpt20`, Wild Grass `sfknaeoa`.

La terre, le sable et la roche réemploient les cartes PBR déjà fournies dans le projet. La couche Pavage sert de surface minérale de réservation ; les joints et bordures architecturales seront construits par modules lors de l'aménagement du quartier. Les instances exposent taille de répétition, teinte et rugosité. Les textures sources restent intactes ; les copies portent leur provenance.

Le Landscape construit sa représentation **Nanite** après l'application des matériaux. Aucun déplacement de matière ni RVT n'est ajouté à cette passe. Les reliefs et les collisions viennent du terrain. La surface d'eau suit séparément les niveaux de la baie, de la rivière et du bassin.

## 3. Végétation

Les familles Fab utilisées sont Wild Grass `vlkhcbxia`, Wild Grass `vczndjqja`, Ribbon Grass `tbdpec3r` et Wheat Grass `tdcrdbur`. Le placement utilise leurs **FoliageTypes natifs** et leurs meshes Nanite au maître, avec une graine déterministe. La variante de blé couchée est réservée à une future passe de débris.

Une couverture initiale espacée occupe Q07, puis des plantations plus denses habillent trois jardins, une prairie et la berge du bassin. Les routes, parcelles bâties réservées, surfaces immergées et fortes pentes sont exclues. Cette distribution est une première passe paysagère locale ; aucune optimisation générale des quartiers n'est entreprise.

Les fichiers d'origine dans `/Game/Fab` ne sont pas modifiés. Les FoliageTypes propres à Arenarea sont copiés sous `/Game/CapitalLandscape/Arenarea/Foliage`. Les identifiants et chemins des assets acquis par l'utilisateur sont consignés dans l'inventaire ; cette livraison ne redistribue pas les fichiers Fab et ne prétend pas vérifier les conditions de son acquisition.

## 4. Vérification et reprise

Les rapports de chaque phase se trouvent sous `Saved/Jadg/arenarea-landscape`. Le plan `plan-relief.png` montre l'ensemble du quartier. Les captures du moteur sont attendues sous `Saved/Captures/arenarea-landscape`, aux cadrages joueur, à midi et à 22 h. L'audit relit le niveau sauvegardé, vérifie les ressources Nanite et compare les contacts physiques à des points du relief.

La carte comporte une zone d'inspection jouable de **180 × 180 m** près du parvis. L'ensemble du quartier se parcourt dans l'éditeur ; cette livraison ne certifie pas encore un réseau de navigation et de quêtes sur 6,127 km². Les franchissements et les constructions seront ajoutés dans leur propre passe.

La chaîne se rejoue depuis le dossier du projet :

```powershell
pwsh scripts/maps/review_arenarea_landscape.ps1 -Phase Relief
pwsh scripts/maps/review_arenarea_landscape.ps1 -Phase Materials
pwsh scripts/maps/review_arenarea_landscape.ps1 -Phase Foliage
pwsh scripts/maps/review_arenarea_landscape.ps1 -Phase Review
```

`-Phase All` exécute ces étapes dans cet ordre, pour **Arenarea seulement**. Repartir de Relief pour remplacer la plantation complète. Fermer le projet dans Unreal avant la reconstruction. Chaque phase s'arrête sur une erreur ; aucune construction concurrente du projet n'est lancée.

L'adaptateur d'éditeur `JadgFoliageBuild` rattache chaque plante à son composant Landscape, comme une plantation peinte. Il évite l'appel Python générique qui laisse cette base vide dans Unreal 5.8.3. Le module du projet doit être compilé avant la première passe Foliage. Les fichiers temporaires de la chaîne restent sous `Saved/Jadg/arenarea-landscape/Temp` sur le disque du projet.

Les producteurs sont `prepare_arenarea_landscape.py` (relief et masques), `build_arenarea_water.py` (surface d'eau), `arenarea_landscape_materials.py` (matières), `inspect_arenarea_fab.py` (inventaire), `prepare_arenarea_foliage.py` (plantation) et `build_arenarea_landscape.py` (construction et audit dans Unreal). La recherche de référence reste [Matériaux et terrains de la capitale](../Recherche/materiaux-terrains-capitale.md).

État de la vérification visuelle : en cours de construction.
