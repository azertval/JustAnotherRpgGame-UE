+++
id = "LOT-1019"
titre = "La chaîne de décor au niveau du moteur, et le standard 3D réécrit"
version = "0.0.3"
filiere = "standard"
statut = "a-faire"
taille = "L"
resume = "Chaque famille de pièces d'un lieu se produit au maître, avec sa matière complète, et s'installe dans le moteur par script ; le standard 3D dit sur mesures ce qu'une pièce doit être."
prerequis = ["LOT-1018"]
livrables = [
  "`style-3d.md` réécrit : §1 géométrie (unité, origine, caméra libre, échelle du décor), §3 poids (sur disque, mesuré), §4 matières (cartes PBR complètes, textures compressées par le moteur, pas de JPEG), §6 familles (les dix familles relues : ce qui vient de Meshy, ce qui vient des bibliothèques du moteur — D-55 —, ce qui se compose), §7 supprimé (plus d'image tolérée dans le décor), §8 les questions tranchées ou renvoyées.",
  "Le gabarit de commande d'une zone (`gabarit-commande-zone.md`) révisé pour commander des pièces au maître, toutes faces, sous une caméra qui tourne.",
  "`import_scenery_unreal.py` : une pièce Meshy ou une pièce des bibliothèques entre dans le projet par script, avec son manifeste (emprise, classe, lumières, matière) ; la vue Scenery de l'atelier (LOT-1008, reportée) livrée sur ce script.",
  "Une **famille témoin** produite au nouveau standard — les façades d'Arenarea, six variantes au moins — rendue sur le parvis de la porte à midi et à 22 h, comparée à la carte peinte et aux captures du 7 octobre.",
  "Le contour sombre, la forme de chaque famille et le budget d'un maillage de décor, que le standard renvoyait au LOT-151, tranchés ici sur captures.",
  "`material_maps.py` et la chaîne procédurale Blender des boîtes d'Arenarea retirés ; les kits republiés portent des maillages au maître.",
]
criteres = [
  "La famille témoin est validée par l'auteur sur le rendu du moteur, à midi et à 22 h, aux cadrages du joueur, comme « au niveau de la carte peinte » (jugement de l'auteur).",
  "Le standard ne contient que des valeurs mesurées sur ce lot ou des décisions datées ; aucune valeur reprise du standard précédent sans remesure.",
  "Une pièce s'installe par script depuis sa fiche sans geste dans l'éditeur ; `check_orphans.py` cite chaque pièce installée.",
  "Le poids du kit témoin et le nombre de triangles de sa plus grosse pièce sont écrits dans la fiche (leçon 3 du bilan de la `0.0.2.5`).",
]
+++

## Pourquoi

Un moteur de ce niveau ne rend bien que des assets de ce niveau (R-15). Soixante modules
d'Arenarea sortent d'un script Blender en boîtes ; les cinq pièces qui ressemblent à l'image
viennent de Meshy. Ce lot renverse la proportion et écrit ce qu'une pièce doit être, sur mesures,
avant qu'Arenarea ne se reconstruise.

## Périmètre

Dedans : le standard, le gabarit de commande, l'import par script, la vue Scenery, une famille
témoin, les questions laissées par le LOT-151.

Dehors, nommément :

- Arenarea entier (LOT-1021) : une famille suffit à écrire le standard ;
- les personnages (LOT-1015), qui ont leur page ;
- le kit commun de la Capitale (LOT-151) : il se produit à la `0.0.4`, au standard écrit ici.

## À supprimer

| Quoi | Où | Pourquoi maintenant |
|---|---|---|
| La chaîne procédurale Blender d'Arenarea (`build_architecture.py`, `build_details.py`, `place_details.py`) | `Tools/Assets3D/.../Production147/` (atelier local) et leurs copies sous `scripts/assetsGeneration/` | elle produit des boîtes que le standard interdit |
| `material_maps.py` (cartes dérivées d'une couleur de base) | `scripts/assetsGeneration/` | une pièce livre ses vraies cartes, ou se recommande |
| §7 du standard 3D, les images tolérées | `Planning/standards/style-3d.md` | plus aucune image ne se dresse sous une caméra libre (D-49) |

Les kits `arenarea@3`, `martpart@4` et `capital/Common@3`, en images et en boîtes, restent lus par
l'ancien moteur jusqu'à la recette ; leur retrait est au LOT-1023.

## Conception

- **Meshy pour l'architecture et le mobilier**, au maître, PBR activé : la décision du 2 octobre
  (« réduction par `reduce_model.py` ») tombe avec D-53. Une pièce se commande depuis une image
  peinte au style du lieu, vue de trois quarts, toutes faces finies.
- **Les bibliothèques du moteur pour la nature** (D-55, tranchée) : sols, roches, végétation,
  matières de base viennent de Megascans ou de Fab ; l'architecture, le mobilier et les personnages
  restent produits pour le lieu. Chaque pièce de bibliothèque est citée par son manifeste avec sa
  licence et son identifiant, et `check_orphans.py` la contrôle comme une pièce Meshy.
- **Les textures** sont compressées par le moteur à l'import (BC7, BC5 pour le relief) ; le kit
  porte les sources (PNG) et le projet leurs sorties régénérées.
- **La facture peinte** (critère de l'auteur du 23 septembre, §5) reste le critère de style : les
  matières sont propres, sans grain ; le contour sombre se juge ici avec et sans.
- **Le lieu se juge sur le rendu du moteur, pas sur une image** : leçon 1 du bilan de la `0.0.2.5`,
  et D-54.

## Risques et questions ouvertes

- **Le coût Meshy.** Trente crédits par pièce au barème des personnages ; une famille de six
  variantes en coûte deux cents. Le relevé du coût par pièce manque toujours (leçon 5 du bilan) :
  ce lot l'écrit pour la famille témoin.
- **Toutes faces.** Une pièce vue sous une caméra qui tourne n'a plus de dos caché ; les retours
  Meshy ont parfois un dos pauvre. Le gabarit de commande le demande ; le contrôle le vérifie sur
  quatre captures.
