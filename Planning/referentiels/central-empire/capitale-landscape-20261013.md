# Capitale — réalisation du Landscape du 13 octobre 2026

**Historique du premier passage.** La correction de relief demandée ensuite
est décrite dans [la reprise du relief](capitale-relief-reprise-20261013.md).
Les chiffres ci-dessous concernent cette première réalisation sauvegardée.

Cette révision construit le niveau `/Game/Maps/Levels/capital-landscape/ensemble`
et le témoin `/Game/Maps/Levels/capital-landscape/material-witness`. C'est une
première composition urbaine construite, pas une approbation artistique des
80 lieux. Les détails individuels et plusieurs contrôles restent ouverts.

## Sources et autorisation

L'auteur a explicitement autorisé une révision des hauteurs du terrain et du
bâti, sous réserve de préserver les fonctions, voisinages et parcours. Les
anciennes plages d'Arenarea/Martpart sont donc des points de départ.

Le catalogue de 80 fiches, les `reference.json`, les planches par lieu et le
panorama v04 viennent de `D:/Codex/2026-10-11/references-capitale`. La carte
source est `D:/JustAnotherDnDGame/Documentation/SourceBook/VTT/Map - Capital.jpg`.
La comparaison de carte est une sortie de contrôle ; aucune de ces images
n'est installée comme décor ou texture dans Unreal.

Les faits et relations des fiches sont recopiés comme données dans
`Saved/Jadg/capital-landscape/references-80.json`, avec leurs empreintes.
Le relevé des positions a une tolérance annoncée de ±15 unités du plan.
Les altitudes, silhouettes nouvelles et implantations non attestées sont des
propositions réversibles, non des dimensions canoniques.

## Terrain, coordonnées et transformations

L'emprise reste 3 024 × 2 016 m : 1 512 × 1 008 quads de 2 m, 24 × 16 composants.
Un seul Landscape ; eau à −2,5 m et seuil Arena à 0 m. Droite de la carte = nord
géographique ; bas = est. Le repère Unreal X/Y conserve droite/bas de l'image.

La composition des collines emploie leur enveloppe plutôt que leur somme.
Les plateformes et le graphe des rues sont calculés après l'hydrologie.
Les axes marchands visent 8 % ; les contrôles portent sur les hauteurs R16
finales et les tabliers, et signalent toute portion au-dessus de 12 %.
Le seuil d'arène est fixé sur les sommets nécessaires à son interpolation.
Les portes reçoivent un terre-plein sec. Les rives ne sont pas comblées par
le nivellement routier. Les bordures terrestres de la carte ne sont plus
abaissées artificiellement au niveau marin.

L'Arena, le casino, Dusk of Justice et l'Hippodrome sont translatés comme
ensembles rigides depuis leurs ancres locales. Le marché et Illu Die sont
posés séparément. L'échelle est 1 ; les déplacements sont consignés dans
`urban-placement.json`. Les distances des anciennes cartes détaillées ne
sont pas projetées telles quelles sur le plan global. Leurs quêtes et
parcours intérieurs demeurent dans leurs cartes détaillées respectives.

Dusk of Justice reçoit en plus une translation proposée de −38 m sur X,
consignée comme `artisticOffsetMetres` : sa première implantation obstruait
le seuil de l'arène et rendait toutes les destinations inaccessibles. La
translation et l'extension du volume de navigation à Eastern Bridge
rétablissent les 17 destinations contrôlées, sans redimensionner le bâtiment.

Water Gate est sec ; Market Gate conserve sa rue extérieure bâtie ; les
trois ponts routiers ont des tabliers distincts de l'aqueduc. Les souterrains
X12/X13 n'ont ni bâtiment ni entrée inventée. Praharebaagh est réservé sans
statue livrée ; son raccord terrestre n'est pas présenté comme certain.

## Matériaux et provenance

| Ressource inspectée dans UE 5.8 | Décision de cette révision |
|---|---|
| SenseiTerrain : parent et deux exemples, fonctions exportées | Conserver la copie portée au Landscape ; ne pas assigner le parent Mesh Terrain source |
| BlendMasterMaterial : quatre variantes, Nanite et VT compris | Lire paramètres/dépendances ; aucune migration générale vers ce parent |
| UE5Landscape : cinq parents/instances | Comparaison de graphes Landscape/Height/RVT ; pas de remplacement sans essai visuel et coût mesuré |
| CastleAssets : sept matériaux, dont HouseWall/CastleMaster/Landforms/eau | Chargement 5.8 avec Bridge désactivé ; pas de copie des bâtiments ni de conversion des sources |
| IntroUnrealProject | Inventaire des exemples d'éclairage et de leurs matériaux ; sources conservées |
| tuto | Aucun asset Content trouvé lors du relevé ; aucune ressource sélectionnée |

Ces contrôles prouvent un chargement et une inspection des graphes, pas la
compatibilité visuelle de toutes les scènes des anciens projets. Les rapports
et graphes `.copy` sont sous `Saved/Jadg/capital-landscape/audit/packs`.

`install_terrain_packs.py` installe SenseiTerrain et les textures GravellySand,
Grass1 et RockVkmfaek. Le complément
`scripts/assetsGeneration/install_capital_surface_sources.py` restaure, si
absents, les paquets MossyGrass/ForestGround requis depuis le projet local
UE5Landscape, vérifiés par
`Source/Elements/Assets/Library/capital-surface-sources.json`. Il ne remplace
pas les textures déjà sauvegardées par Unreal et ne modifie pas les packs.
BeachCliff, MossyCreekStones et Mossy_Rocky_Ground_vcrkeax sont catalogués avec
leurs chemins et empreintes mais ne sont pas adoptés dans les cinq couches.
Grass1 est installé par l'outil de pack mais n'est pas branché au Landscape.

La couche D est désormais une vraie terre procédurale ; l'ancien sol moussu
rocheux reste sur disque. Trois variantes de terre, pavés et sol humide sont
produites par `capital_surface_materials.py`. Les champs physiques et les
pigments sont indépendants : aucune hauteur, normale ou roughness n'est
extraite de la luminosité de l'albedo.

- BC : sRGB, BC7. ORM : linéaire, BC7, R=AO/G=roughness/B=metallic.
- Normales : Normalmap ; les nouvelles sources sont DirectX, sans inversion.
  La chaîne glTF garde son inversion OpenGL ; gravelly_sand_nor_dx reste
  DirectX. `normalScale` pilote maintenant réellement `NormalStrength` dans
  les deux parents M_Scenery.
- H : 16 bits à la source, R16F importé ; neutre 0,5 et plage 2 cm pour les
  nouvelles surfaces. Herbe A et sous-bois C gardent une hauteur grise de
  secours, explicitement manquante.
- `Size=0,5` signifie une répétition proche de 2 m après la conversion
  position cm × 0,01 du graphe. Les paramètres lointains restent distincts.
- Les textures de hauteur B/D/E alimentent aussi `Height Blend` ; les masques
  B–E restent des recouvrements empilés. Le déplacement du Landscape est nul.
- Les finitions de maçonnerie, bois, bronze, marbre et tissus réutilisent les
  instances peintes du témoin Arena. Les nouvelles toitures vertes et bleues
  ont leurs propres instances. Plusieurs surfaces restent trop uniformes à
  l'échelle architecturale et demandent une passe de détail.
- Quatre instances d'eau règlent séparément roughness, absorption, diffusion,
  vitesses, longueurs et force des vagues. Leurs surfaces sont non Nanite :
  le premier rendu avait démontré l'incompatibilité Single Layer Water/Nanite.
  Les composants interdisent explicitement Nanite. L'export impose des
  normales vers le haut après le recalcul des faces ouvertes ; les quatre
  GLB corrigés ne contiennent plus de normale descendante.
- La végétation géométrique a un parent Two Sided Foliage et de la transmission.
  Les plantations sont déterministes et excluent routes, ouvrages et seuils.
  Le vent et ses fondus ne sont pas livrés.
- Physical Materials terre/pavés/humide : frictions proposées 0,65/0,65/0,45.
  Les sons de pas spécifiques ne sont pas intégrés.

L'audit final énumère les paramètres réellement lus, les textures, les
matériaux employés par les composants et les réglages Nanite/Lumen/VSM/VT/
Substrate. Un suffixe VT ne vaut pas preuve d'un raccord RVT opérationnel.

## Construction et contrôle reproductibles

Prérequis : UE 5.8.3, Blender 5.2, la cible d'éditeur compilée, le `.venv`, les
packs locaux, et les assets détaillés déjà produits d'Arenarea/Martpart.
Recompiler la cible après les ajouts à `JadgCaptureDirector` (filtrage
`-JadgShots`) et `JadgSceneBuild` (entrée Displacement masquée à Python).

```powershell
pwsh scripts/maps/review_capital_landscape.ps1
```

Cette commande prépare le relief, les surfaces et l'implantation ; génère les
GLB avec `scripts/assetsGeneration/build_capital_urban_assets.py` ; contrôle
la géographie ; construit les deux niveaux ; rend midi/22 h ; mesure quatre
vues ; audite les matériaux ; produit la galerie. `-SkipPrepare -SkipBuild`
rejoue les captures d'un niveau déjà construit. Un seul Unreal à la fois.

Sources nouvelles : `capital_city_layout.py`, `capital_urban_terrain.py`,
`capital_urban_scene.py`, `capital_surface_materials.py`,
`build_capital_material_witness.py`, `review_capital_geography.py`,
`review_capital_navigation.py`, `audit_capital_landscape.py`,
`audit_capital_packs.py`, `report_capital_review.py`. Le test de contrat
est `scripts/tests/test_capital_urban_contract.py`.

L'audit des projets sources se lance dans chaque projet via le commandlet
Python Unreal avec `-script=E:/JustAnotherRpgGame_UR/JustAnotherRpgGame/scripts/maps/audit_capital_packs.py`.
Les projets IntroUnrealProject et CastleAssets nécessitent aussi
`-DisablePlugins=Bridge -EnablePlugins=PythonScriptPlugin` pour ce relevé.

Sorties : `Saved/Jadg/capital-landscape/review.html`, `heights-final.json`,
`references-80.json`, `engine-built.json`, `geography-review.json`,
`navigation-review.json`, `performance-final.json`, `audit-after/engine-after.json`.
Les images fraîches sont sous `Saved/Captures/capital-landscape/final` ; les
anciens rendus et la première passe de correction restent séparés. La sauvegarde
initiale est `Saved/Jadg/capital-landscape/baseline-20261013`.

## Limites à conserver visibles

Les formes nouvelles de cathédrale/palais/tour sont des propositions, et les
institutions secondaires sont souvent encore des assemblages génériques.
La correspondance des 80 références ne prouve pas leur fidélité architecturale.
Les hauteurs de façade/toiture proposées ne doivent pas être confondues avec
les bounds totaux mesurés. Les niveaux de rues se lisent dans les profils,
pas automatiquement dans l'altitude de l'ancre d'un bâtiment.

La navigation extérieure emploie des cellules de 40 cm, tuiles de 96 m et
contrôle des destinations sur la collision réelle. Ses résultats sont livrés,
y compris les cibles non atteintes ; ce n'est pas une validation de marche
jouée ni des intérieurs, des marches fines ou de chaque rue secondaire.

Le témoin de matériaux comporte un volume arrondi servant d'éprouvette,
pas un rocher final. Le contact sec/humide doit encore devenir une transition
continue. Deux pavages comparent un déplacement nul et une plage de 2 cm ;
leur collision demeure inchangée. L'entrée est connectée par l'API native
car MP_Displacement est Hidden dans UE 5.8.
`r.Nanite.AllowTessellation` vaut 0 dans la configuration de la capitale.
Le processus du témoin surcharge seulement cette option à 1 ; une capture
séparée la laisse à 0. La présence des paramètres ne vaut pas, seule, preuve
d'un déplacement visible. Les buffers BaseColor, Roughness, WorldNormal et
Metallic du témoin sont rendus séparément ; ils ne couvrent pas chaque
matériau des quartiers.
Les deux processus de comparaison ont terminé après exclusion de l'eau du
témoin de Nanite. L'écart visuel de la dalle reste subtil : l'amplitude rendue,
les raccords et le coût du déplacement ne sont pas déclarés validés.

Les mesures finales à 1 920 × 1 080 sur RTX 4060 Ti donnent, à midi / 22 h :
ensemble 71,5 / 74,5 images/s ; Water Gate 65,0 / 71,2 ; Market Gate–Old Bridge
44,7 / 46,2 ; Scholarnest–Dweomer 55,7 / 58,8. La cible de 60 images/s n'est
donc pas atteinte dans toutes les vues. Les p99 et temps GPU se trouvent dans
`performance-final.json` ; ce relevé ne représente pas un parcours de jeu.

La carte reste un niveau classique. Les 9 840 objets sont regroupés quand
possible en 306 ensembles d'instances, sur 131 maillages distincts. Cette
organisation conserve les outils de capture et de navigation existants.
Aucune mesure de chargement de cellules ni de transition HLOD n'a été faite :
la conversion World Partition n'est donc pas déclarée validée. Le streaming
VT est actif, mais aucun volume RVT terrain–décor n'est installé. Son adoption
nécessiterait un témoin mesurant couleur/roughness et normales monde écrites
par le terrain, lecture au pied des décors, résolution et coût ; cette
expérience n'est pas livrée.

Le contrôle global initial signalait 79 orphelins. La référence manquante
à l’audit des packs a été ajoutée ; il reste 78 assets orphelins, dont des ressources
préexistantes SenseiMaterials/Tutorial et NewMap. Aucun de ces fichiers
étrangers à cette révision n'a été supprimé. Ce contrôle global ne doit pas
être présenté comme réussi.

RVT, World Partition/HLOD, tous les buffers de chaque matériau, validation
exhaustive du déplacement, faune, statue du tigre, métiers, vie domestique,
détails des institutions et habillage des bords du terrain restent ouverts.
Les performances doivent être lues dans les mesures de cette scène, sans
reprendre les résultats de l'ancienne porte ou d'un quartier isolé.
