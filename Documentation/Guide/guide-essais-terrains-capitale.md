# Essais de terrain de la capitale

Trois prototypes autonomes du 15 octobre 2026, construits depuis des descriptions texte.
Chaque Landscape mesure 126 × 126 m, avec quatre composants de 63 quads au pas de 1 m.
Ce sont des assemblages de démonstration, pas des morceaux géoréférencés de la ville complète.

| Niveau dans `Content/Maps/Levels/essai` | Démonstration |
|---|---|
| `capitale-sols-urbains` | Trois pavages répétables, bordures droite et angle, terrasse, mur, rampe et escalier ; référence de sol +20 m |
| `capitale-rives` | Quais à +3,5 m, eau à 0, bande humide, sable, rochers et raccord de berge |
| `capitale-terres-roches` | Terre cultivée, sillons, chemin, herbe et affleurements rocheux autour de +30 m |

Le cadrage `ensemble` présente chaque assemblage ; les deux cadrages suivants montrent les
matières et raccords dans les bornes de la caméra du joueur. Les petits poteaux sont des repères
de 2 m, espacés de 1,5 m. Les lampes sont des éclairages d'atelier proposés, pas de nouveaux
réglages artistiques approuvés pour la capitale.

## Reconstruction

Fermer l'éditeur avant la reconstruction. Un seul processus Unreal travaille sur le projet.

```powershell
pwsh scripts/maps/review_capital_terrain_labs.ps1
```

Ce point d'entrée appelle `scripts/assetsGeneration/build_capital_terrain_modules.py` dans
Blender, puis `scripts/maps/build_capital_terrain_labs.py --prepare`, construit les assets
dans Unreal et capture les trois cartes à midi et à 22 h. `-SkipPrepare`, `-SkipBuild` et
`-SkipCapture` permettent de reprendre une phase. Aucune logique Blueprint n'est créée.

Les sources géométriques sont sous `Source/Elements/Assets/Built/capital-terrain-labs` ;
leur `manifest.json` cite les 13 GLB générés. Les descriptions de cartes sont sous
`Source/Test/Fixtures/Exploration/Levels/essai`. Tous les binaires Unreal se régénèrent.

## Matériaux et Nanite

Les assets de ce lot sont isolés sous `/Game/CapitalTerrainLabs` : `Materials`, `Textures`,
`Meshes`, `Layers`. `capital_terrain_lab_materials.py` construit un parent Landscape natif
et cinq familles de matériaux de mesh. L'instance `MI_Landscape_Capitale` expose cinq couches :
**Herbe, Terre, Sable, Roche, Humide**. Les poids importés totalisent exactement 255 à chaque
sommet ; les mêmes couches pilotent couleur, normale et rugosité. Les terrains restent peignables.

Les tailles de répétition, teintes, normales et rugosités sont des paramètres. Les textures
viennent des packs déjà installés : MossyGrass, ForestGround, GravellySand et RockVkmfaek.
Des copies locales au lot fixent sRGB pour la couleur, linéaire pour les données, BC5 pour
les normales et BC7 pour couleur/rugosité. Les originaux restent intacts. La métadonnée
`CapitalTerrainLabSource` désigne leur chemin ; la provenance locale est documentée par
`Source/Elements/Assets/Library/capital-surface-sources.json` et `install_terrain_packs.py`.
Aucune licence ni origine Fab non vérifiée n'est attribuée à ces fichiers.

Le Landscape emploie des coordonnées monde XY ; les meshes emploient leurs UV métriques
orientées par face. Ce premier lot ne prétend pas fournir un mélange RVT ou une projection
triplanaire des normales. Les raccords sont géométriques : bords enfouis, joints, bordures et
bandes de matériaux. Le relief des pavés et rochers est dans les meshes. La couche Humide
réemploie ForestGround avec teinte et rugosité réglées ; ce n'est pas un nouveau scan.

Nanite est construit sur les 13 modules et sur chaque Landscape. Le rapport distingue les
triangles Nanite réels, sans les remplacer par le nombre de triangles du fallback. L'eau reste
une surface séparée. La tessellation dynamique et le RVT ne sont pas activés dans ces témoins.
Les collisions complexes des modules reposent sur leur fallback ; Nanite ne certifie pas
la navigabilité d'un assemblage. Les pentes et accès de ces prototypes sont à éprouver avant
réemploi dans une rue ou un trajet de foule.

## Revue

Les rapports sont sous `Saved/Jadg/capital-terrain-labs`, les images sous
`Saved/Captures/capital-terrain-labs`. Une construction réussie exige des données Nanite
effectivement présentes et les trois cartes sauvegardées. Les captures sont vérifiées sur
leur fraîcheur ; une compilation de matériau en échec bloque la recette.

La recherche de référence est [Matériaux et terrains de capitale](../Recherche/materiaux-terrains-capitale.md).
Ses recommandations couvrent aussi des techniques de comparaison qui ne sont pas toutes
activées ici. Les choix artistiques des nouveaux essais restent soumis au jugement de l'auteur.
