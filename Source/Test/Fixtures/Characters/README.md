# Le modèle d'essai animé

Les données d'essai du `LOT-1005` : un **vrai** modèle de personnage, lié au squelette humanoïde
commun, pour que le moteur anime autre chose qu'un pantin de trois os.

| Fichier | Contenu |
|---|---|
| `Assets/Common/Characters/Mannequins/humanoid/humanoid.glb` | le mannequin humanoïde de l'atelier, réduit à 4 000 triangles et à une texture de 256 px (0,6 Mio), lié aux 53 os, avec ses six clips |
| `Assets/Common/Characters/Skeletons/humanoid/skeleton.json` | la description du squelette : les 53 os, et par clip sa durée, sa boucle et son image clé |

**Rien ne s'y retouche à la main.** Les deux fichiers sont sortis, le 2 octobre 2026, de la chaîne de
liaison de l'ancien moteur (`rig_character.py`, retirée au `LOT-1015` par D-64 : un personnage du
jeu est désormais une fiche d'apparence que le créateur du moteur assemble). Ils restent ici comme
**données d'essai du lecteur `.glb` de Core** (`Core/Resources/MeshFile`), qui lit un maillage lié,
ses os et ses clips ; ils ne décrivent plus un personnage du jeu et ne se régénèrent pas.
